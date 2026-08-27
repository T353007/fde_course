package com.northstar.underwriting.decision;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.northstar.common.model.BankTransaction;
import com.northstar.underwriting.config.FeatureFlags;
import com.northstar.underwriting.revenue.RevenueCalculator;
import com.northstar.underwriting.revenue.RevenueCalculatorV2;

/**
 * Debt service coverage ratio. Caller number two of the revenue function.
 *
 * <p>DSCR is net operating income divided by debt service. If it is below 1.25 the business
 * cannot comfortably cover the payment, and policy says decline.
 *
 * <p>This service wants operating revenue. It calls
 * {@link RevenueCalculator#calculateMonthlyRevenue}, which returns every credit. So the
 * input is too high, and because DSCR multiplies revenue by a margin and then divides, the
 * error does not stay the same size. It gets amplified by the margin step and then decides
 * a threshold.
 *
 * <p>Worked example, using the sample statement everyone at Northstar has seen:
 *
 * <pre>
 *   total credits for the month ............ 252,400
 *   correct operating revenue .............. 147,400
 *     (excludes a 30,000 transfer from savings and a 75,000 Fastcapital loan deposit)
 *
 *   net operating income at 18 percent margin
 *     from total credits ................... 45,432
 *     from operating revenue ............... 26,532
 *
 *   monthly debt service ................... 30,000
 *
 *   DSCR from total credits ................ 1.51   passes
 *   DSCR from operating revenue ............ 0.88   declines
 * </pre>
 *
 * <p>The revenue number is 71 percent too high. The DSCR lands on the other side of the
 * threshold. That is the compounding. A file that should decline gets approved, and the
 * decision record shows a clean 1.51 with no sign anything is wrong.
 *
 * <p>The 18 percent margin is its own problem. See the constant.
 */
@Service
public class DebtServiceCoverageService {

    private static final Logger log = LoggerFactory.getLogger(DebtServiceCoverageService.class);

    /** Policy floor. credit-policy-2025.pdf section 4.1. This one is correct. */
    public static final BigDecimal DSCR_FLOOR = new BigDecimal("1.25");

    /**
     * Assumed net operating margin, used when we do not have a tax return.
     *
     * <p>18 percent came from a 2016 portfolio study of 400 files. It has never been redone.
     * It is applied to restaurants and to software companies at the same rate.
     */
    private static final BigDecimal ASSUMED_OPERATING_MARGIN = new BigDecimal("0.18");

    private final RevenueCalculator revenueCalculator;
    private final RevenueCalculatorV2 revenueCalculatorV2;
    private final FeatureFlags featureFlags;

    public DebtServiceCoverageService(RevenueCalculator revenueCalculator,
                                      RevenueCalculatorV2 revenueCalculatorV2,
                                      FeatureFlags featureFlags) {
        this.revenueCalculator = revenueCalculator;
        this.revenueCalculatorV2 = revenueCalculatorV2;
        this.featureFlags = featureFlags;
    }

    /**
     * Computes DSCR for an application.
     *
     * @param transactions      bank transactions for the statement period
     * @param months            months of statement history
     * @param monthlyDebtService existing debt payments plus the proposed payment
     */
    public BigDecimal computeDscr(List<BankTransaction> transactions, int months, BigDecimal monthlyDebtService) {
        if (monthlyDebtService == null || monthlyDebtService.signum() <= 0) {
            // No debt means infinite coverage. Returning a big number is not great, but the
            // reviewer portal renders null as "n/a" and underwriters read that as an error.
            return new BigDecimal("99.9999");
        }

        BigDecimal monthlyRevenue = resolveMonthlyRevenue(transactions, months);

        // Step one. Turn revenue into an income estimate.
        BigDecimal netOperatingIncome = monthlyRevenue
                .multiply(ASSUMED_OPERATING_MARGIN)
                .setScale(2, RoundingMode.HALF_UP);

        // Step two. Divide by the payment. Any error in revenue is now scaled by the margin
        // and then compared against a hard threshold.
        BigDecimal dscr = netOperatingIncome.divide(monthlyDebtService, 4, RoundingMode.HALF_UP);

        log.debug("dscr computed revenue={} noi={} debtService={} dscr={}",
                monthlyRevenue, netOperatingIncome, monthlyDebtService, dscr);

        return dscr;
    }

    public boolean passesPolicyFloor(BigDecimal dscr) {
        return dscr != null && dscr.compareTo(DSCR_FLOOR) >= 0;
    }

    /**
     * Picks which revenue calculator to use.
     *
     * <p>This block is copied from UnderwritingDecisionService. When the flag was added
     * there was no shared place to put it, and there still is not. The two copies have
     * drifted: that one logs the delta between V1 and V2, this one does not.
     */
    private BigDecimal resolveMonthlyRevenue(List<BankTransaction> transactions, int months) {
        if (featureFlags.isUseNewRevenueCalcV2Temp()) {
            return revenueCalculatorV2.calculateMonthlyRevenue(transactions, months);
        }
        return revenueCalculator.calculateMonthlyRevenue(transactions, months);
    }
}
