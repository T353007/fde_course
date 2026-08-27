package com.northstar.underwriting.revenue;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import com.northstar.common.model.BankTransaction;

/**
 * The replacement for RevenueCalculator. Half finished.
 *
 * <p>The idea was to exclude the credits that are not revenue, which is what underwriting
 * has asked for since 2019. Two of the three exclusions work:
 *
 * <ul>
 *   <li>Loan proceeds. The keyword list below catches the common lenders, including
 *       Fastcapital, which shows up in a surprising number of files.
 *   <li>Internal transfers. Handed off to {@link InternalTransferDetector}, which only
 *       understands First Carolina Bank statements. For every other bank the transfer is
 *       still counted.
 * </ul>
 *
 * <p>The third exclusion was never started. Card processors sometimes deposit gross and
 * then claw back fees as a separate debit, and sometimes deposit net. Counting gross on the
 * first kind and net on the second overstates one merchant against another. Renee adjusts
 * for this by hand. There is no code for it.
 *
 * <p>This class is gated behind the USE_NEW_REVENUE_CALC_V2_TEMP flag, which is false in
 * every environment. It has been false since the flag was added in March 2021. Turning it
 * on moves numbers, so it needs a real backtest against the last two quarters of decisions
 * before anyone flips it. That backtest was never run.
 *
 * <p>dpatel, 2021-03-11. Last real change 2021-04-02.
 */
@Component
public class RevenueCalculatorV2 {

    private static final Logger log = LoggerFactory.getLogger(RevenueCalculatorV2.class);

    /**
     * Descriptions that mean "somebody lent this business money".
     *
     * <p>Grown by hand as files came in. It is not a policy list and it is not reviewed by
     * anyone in credit. FASTCAPITAL is on it because five files in the 2021 sample had a
     * Fastcapital loan deposit and all five were counted as revenue by V1.
     */
    private static final List<String> LOAN_KEYWORDS = List.of(
            "FASTCAPITAL",
            "LOAN PROCEEDS",
            "LOAN ADVANCE",
            "LOAN DISBURSEMENT",
            "SBA LOAN",
            "MERCHANT ADVANCE",
            "MCA FUNDING",
            "ONDECK",
            "KABBAGE",
            "BLUEVINE");

    private final InternalTransferDetector transferDetector;

    public RevenueCalculatorV2(InternalTransferDetector transferDetector) {
        this.transferDetector = transferDetector;
    }

    /**
     * Same signature as V1 on purpose, so the switch is a one line change.
     *
     * @return average monthly operating revenue, minus the exclusions that are implemented
     */
    public BigDecimal calculateMonthlyRevenue(List<BankTransaction> transactions, int months) {
        if (months <= 0) {
            return BigDecimal.ZERO;
        }

        BigDecimal total = BigDecimal.ZERO;
        List<String> excluded = new ArrayList<>();

        for (BankTransaction t : transactions) {
            if (t.amount() == null || t.amount().signum() <= 0) {
                continue;
            }

            ExclusionReason reason = classify(t);
            if (reason == ExclusionReason.NONE) {
                total = total.add(t.amount());
            } else {
                excluded.add(reason.name() + " " + t.amount().toPlainString() + " " + t.description());
            }
        }

        if (!excluded.isEmpty()) {
            // Logged so the backtest could diff V1 against V2 without a database change.
            // The backtest was never written, so this log goes nowhere useful.
            log.info("revenue_v2 excluded {} credits: {}", excluded.size(), excluded);
        }

        return total.divide(BigDecimal.valueOf(months), 2, RoundingMode.HALF_UP);
    }

    /** What kind of non revenue credit this is, if any. */
    public enum ExclusionReason {
        NONE,
        LOAN_PROCEEDS,
        INTERNAL_TRANSFER,

        /**
         * Never returned. The netting problem in the class comment would produce this.
         * Left here so the enum shows the intended shape.
         */
        CARD_SETTLEMENT_ADJUSTMENT
    }

    public ExclusionReason classify(BankTransaction t) {
        String description = t.description() == null ? "" : t.description().toUpperCase(Locale.US);

        for (String keyword : LOAN_KEYWORDS) {
            if (description.contains(keyword)) {
                return ExclusionReason.LOAN_PROCEEDS;
            }
        }

        if (transferDetector.isInternalTransfer(t)) {
            return ExclusionReason.INTERNAL_TRANSFER;
        }

        // TODO(dpatel, 2021-04): card settlement netting. See class comment. Needs the
        // processor name and the fee debits matched to the payout, which means grouping by
        // date range. Not started.

        return ExclusionReason.NONE;
    }
}
