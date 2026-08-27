package com.northstar.underwriting.policy;

import java.math.BigDecimal;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import com.northstar.common.money.MoneyAmount;
import com.northstar.underwriting.config.FeatureFlags;

/**
 * The rule engine. The rules are in this file, in Java, as numbers.
 *
 * <p>There are eight policy PDFs in the document store. None of them is loaded by this
 * class. The rules below were typed in from whichever PDF was current when the rule was
 * added, and they have not been checked against the PDFs since. At least two of them
 * disagree with the current policy. Those two are marked.
 *
 * <p>Renee keeps eleven more rules in a spreadsheet on her desktop. Those are not here
 * either.
 */
@Component
public class PolicyRuleEngine {

    private static final Logger log = LoggerFactory.getLogger(PolicyRuleEngine.class);

    /**
     * Minimum time in business, in months.
     *
     * <p>DOES NOT MATCH POLICY. credit-policy-2025.pdf section 3.2 lowered this to 18
     * months for term loans so Northstar could compete with Fastcapital on newer
     * businesses. The code still says 24. Nobody filed a ticket because nobody compared
     * the two. Applications between 18 and 24 months get declined with
     * TIME_IN_BUSINESS_TOO_SHORT, which is why Carla's queue has a steady trickle of
     * "but your website says 18 months" tickets.
     */
    private static final int MIN_TIME_IN_BUSINESS_MONTHS = 24;

    /**
     * Minimum annual revenue, derived by multiplying monthly revenue by 12.
     *
     * <p>Matches credit-policy-2025.pdf. The problem is not the threshold, it is the input.
     * See RevenueCalculator.
     */
    private static final BigDecimal MIN_ANNUAL_REVENUE = new BigDecimal("250000.00");

    /**
     * Product caps.
     *
     * <p>DOES NOT MATCH POLICY for SBA 7(a). SBA-overlay.pdf raised the cap to 500,000 in
     * March 2024. This table still says 350,000, which was the 2019 number. Anything above
     * 350,000 gets referred to manual review, so the deals do still close. They just take
     * four extra days and Hank counts them against his SLA.
     *
     * <p>This is the table that still uses MoneyAmount from the 2018 refactor.
     */
    private static final Map<String, MoneyAmount> PRODUCT_MAX_AMOUNT = Map.of(
            "TERM_LOAN", MoneyAmount.of("750000.00"),
            "LOC", MoneyAmount.of("250000.00"),
            "SBA_7A", MoneyAmount.of("350000.00"),
            "EQUIPMENT", MoneyAmount.of("1000000.00"));

    /** Minimum months of bank statements we need before an automated call is allowed. */
    private static final int MIN_STATEMENT_MONTHS = 3;

    private final FeatureFlags featureFlags;

    public PolicyRuleEngine(FeatureFlags featureFlags) {
        this.featureFlags = featureFlags;
    }

    public PolicyEvaluationResult evaluate(PolicyEvaluationInput input) {
        PolicyEvaluationResult result = new PolicyEvaluationResult();

        // Rule 1. Enough statement history to say anything at all.
        if (input.monthsOfStatementHistory() < MIN_STATEMENT_MONTHS) {
            result.refer("INSUFFICIENT_STATEMENT_HISTORY");
        }

        // Rule 2. Time in business. See the constant, it is wrong.
        if (input.timeInBusinessMonths() < MIN_TIME_IN_BUSINESS_MONTHS) {
            result.decline("TIME_IN_BUSINESS_TOO_SHORT");
        }

        // Rule 3. Revenue floor.
        BigDecimal monthly = input.monthlyRevenue() == null ? BigDecimal.ZERO : input.monthlyRevenue();
        BigDecimal annualized = monthly.multiply(BigDecimal.valueOf(12));
        if (annualized.compareTo(MIN_ANNUAL_REVENUE) < 0) {
            result.decline("ANNUAL_REVENUE_BELOW_MINIMUM");
        }

        // Rule 4. Product cap.
        MoneyAmount cap = PRODUCT_MAX_AMOUNT.get(input.product());
        if (cap == null) {
            // Products get added to the portal before they get added here. It has happened
            // twice. Referring is safer than declining.
            log.warn("no amount cap configured for product {}, referring application {}",
                    input.product(), input.applicationId());
            result.refer("UNKNOWN_PRODUCT");
        } else if (MoneyAmount.of(input.amountRequested()).isGreaterThan(cap)) {
            result.refer("AMOUNT_ABOVE_PRODUCT_CAP");
        }

        // Rule 5. FICO. Missing FICO is treated as a referral, not a decline, because
        // Corveil times out often enough that declining on a timeout would be unfair.
        if (input.ownerFico() == null) {
            result.refer("CREDIT_BUREAU_NO_HIT");
        } else if (input.ownerFico() < 640) {
            result.decline("OWNER_FICO_BELOW_MINIMUM");
        }

        // Rule 6. The California overlay.
        //
        // Added by mfoster in 2019 for the Cascade launch. Michael Foster left Northstar in
        // 2020. The commit message says "per policy" and does not say which policy. There is
        // a California-overlay.pdf in the document store and this rule is not in it. It may
        // have come from a call with Cascade's counsel. If you need to change this, someone
        // has to ask Cascade what the rule actually is.
        if (featureFlags.isCascadeOverlayEnabled()
                && "CASCADE".equals(input.tenantId())
                && "CA".equals(input.stateCode())
                && "LOC".equals(input.product())) {
            result.refer("CA_LOC_MANUAL_REVIEW_REQUIRED");
        }

        if (!result.isDeclined() && !result.isReferToManual()) {
            result.note("PASSED_AUTOMATED_POLICY");
        }

        return result;
    }
}
