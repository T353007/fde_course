package com.northstar.underwriting.decision;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.northstar.common.event.UnderwritingDecisionedEvent;
import com.northstar.common.model.BankTransaction;
import com.northstar.common.tenant.TenantContext;
import com.northstar.underwriting.config.FeatureFlags;
import com.northstar.underwriting.entity.BankTransactionEntity;
import com.northstar.underwriting.entity.DecisionEntity;
import com.northstar.underwriting.fraud.FraudGateway;
import com.northstar.underwriting.kafka.DecisionEventPublisher;
import com.northstar.underwriting.policy.PolicyEvaluationInput;
import com.northstar.underwriting.policy.PolicyEvaluationResult;
import com.northstar.underwriting.policy.PolicyRuleEngine;
import com.northstar.underwriting.repo.BankTransactionRepository;
import com.northstar.underwriting.repo.DecisionRepository;

/**
 * Makes the automated underwriting call. Caller number one of the revenue function.
 *
 * <p>What this service wants is operating revenue: money the business earned. What it gets
 * is total credits, because {@link com.northstar.underwriting.revenue.RevenueCalculator}
 * adds up every deposit. A transfer between the applicant's own accounts counts. A loan
 * from another lender counts. Both inflate the number that the revenue floor rule and the
 * DSCR rule read.
 *
 * <p>Nobody here is confused about what revenue means. The function was written in 2019
 * with a TODO on it, credit policy never answered, and three things now depend on the
 * answer it gives.
 */
@Service
public class UnderwritingDecisionService {

    private static final Logger log = LoggerFactory.getLogger(UnderwritingDecisionService.class);

    /** How many months of history the decision assumes when we cannot tell. */
    private static final int DEFAULT_MONTHS_ASSUMED = 3;

    /** Above this score the file goes to Ada's team no matter what policy said. */
    private static final int FRAUD_REVIEW_THRESHOLD = 700;

    private final BankTransactionRepository bankTransactionRepository;
    private final DecisionRepository decisionRepository;
    private final com.northstar.underwriting.revenue.RevenueCalculator revenueCalculator;
    private final com.northstar.underwriting.revenue.RevenueCalculatorV2 revenueCalculatorV2;
    private final DebtServiceCoverageService dscrService;
    private final PolicyRuleEngine policyRuleEngine;
    private final FraudGateway fraudGateway;
    private final DecisionEventPublisher eventPublisher;
    private final FeatureFlags featureFlags;

    public UnderwritingDecisionService(BankTransactionRepository bankTransactionRepository,
                                       DecisionRepository decisionRepository,
                                       com.northstar.underwriting.revenue.RevenueCalculator revenueCalculator,
                                       com.northstar.underwriting.revenue.RevenueCalculatorV2 revenueCalculatorV2,
                                       DebtServiceCoverageService dscrService,
                                       PolicyRuleEngine policyRuleEngine,
                                       FraudGateway fraudGateway,
                                       DecisionEventPublisher eventPublisher,
                                       FeatureFlags featureFlags) {
        this.bankTransactionRepository = bankTransactionRepository;
        this.decisionRepository = decisionRepository;
        this.revenueCalculator = revenueCalculator;
        this.revenueCalculatorV2 = revenueCalculatorV2;
        this.dscrService = dscrService;
        this.policyRuleEngine = policyRuleEngine;
        this.fraudGateway = fraudGateway;
        this.eventPublisher = eventPublisher;
        this.featureFlags = featureFlags;
    }

    @Transactional
    public DecisionEntity decide(DecisionRequest request) {
        List<BankTransaction> transactions = loadTransactions(request.applicationId());
        int months = request.monthsOfHistory() > 0 ? request.monthsOfHistory() : DEFAULT_MONTHS_ASSUMED;

        // This is the revenue number the whole decision hangs on.
        BigDecimal monthlyRevenue = resolveMonthlyRevenue(transactions, months);

        BigDecimal dscr = dscrService.computeDscr(transactions, months, request.monthlyDebtService());

        PolicyEvaluationInput policyInput = new PolicyEvaluationInput(
                request.applicationId(),
                request.tenantId(),
                request.product(),
                request.stateCode(),
                request.amountRequested(),
                monthlyRevenue,
                months,
                request.timeInBusinessMonths(),
                request.ownerFico());

        PolicyEvaluationResult policy = policyRuleEngine.evaluate(policyInput);

        if (!dscrService.passesPolicyFloor(dscr)) {
            policy.decline("DSCR_BELOW_FLOOR");
        }

        int fraudScore = fraudGateway.getFraudScore(
                request.applicationId(), request.tenantId(), request.legalName(), request.ein());

        if (fraudScore >= FRAUD_REVIEW_THRESHOLD) {
            policy.refer("FRAUD_SCORE_HIGH");
        }

        String outcome = resolveOutcome(policy);

        DecisionEntity entity = new DecisionEntity();
        entity.setApplicationId(request.applicationId());
        entity.setOutcome(outcome);
        entity.setReasonCodes(policy.reasonCodesAsColumn());
        entity.setMonthlyRevenue(monthlyRevenue);
        entity.setDscr(dscr.setScale(4, RoundingMode.HALF_UP));
        entity.setDecidedBy("AUTO_ENGINE");
        entity.setTenantId(request.tenantId() == null ? TenantContext.get() : request.tenantId());
        entity.setCreatedAt(Instant.now());

        DecisionEntity saved = decisionRepository.save(entity);

        eventPublisher.publishDecisioned(new UnderwritingDecisionedEvent(
                saved.getApplicationId(),
                saved.getTenantId(),
                saved.getOutcome(),
                saved.getReasonCodes(),
                saved.getMonthlyRevenue(),
                saved.getDscr(),
                saved.getCreatedAt()));

        return saved;
    }

    private String resolveOutcome(PolicyEvaluationResult policy) {
        if (policy.isDeclined()) {
            return "DECLINED";
        }
        if (policy.isReferToManual()) {
            return "REFER_MANUAL";
        }
        return "APPROVED";
    }

    private List<BankTransaction> loadTransactions(Long applicationId) {
        List<BankTransactionEntity> rows =
                bankTransactionRepository.findByApplicationIdOrderByPostedDateAsc(applicationId);
        return rows.stream().map(BankTransactionEntity::toModel).toList();
    }

    /**
     * Picks which revenue calculator to use.
     *
     * <p>The flag has been false since it was added in 2021. The delta log below was meant
     * to feed a backtest. Nothing reads it. Note that this runs both calculators when the
     * flag is on, which doubles the work on a hot path. That was fine when it was going to
     * be temporary.
     *
     * <p>The same block exists in DebtServiceCoverageService without the delta log.
     */
    private BigDecimal resolveMonthlyRevenue(List<BankTransaction> transactions, int months) {
        BigDecimal v1 = revenueCalculator.calculateMonthlyRevenue(transactions, months);

        if (!featureFlags.isUseNewRevenueCalcV2Temp()) {
            return v1;
        }

        BigDecimal v2 = revenueCalculatorV2.calculateMonthlyRevenue(transactions, months);
        log.info("revenue_calc_delta v1={} v2={} delta={}", v1, v2, v1.subtract(v2));
        return v2;
    }
}
