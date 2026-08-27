package com.northstar.underwriting.policy;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import com.northstar.underwriting.config.FeatureFlags;

class PolicyRuleEngineTest {

    private PolicyRuleEngine engine;
    private FeatureFlags flags;

    @BeforeEach
    void setUp() {
        flags = new FeatureFlags();
        flags.setCascadeOverlayEnabled(true);
        engine = new PolicyRuleEngine(flags);
    }

    private static PolicyEvaluationInput clean() {
        return new PolicyEvaluationInput(
                1001L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("250000.00"),
                new BigDecimal("40000.00"),
                6, 48, 720);
    }

    @Test
    void aCleanFileWithNoProblemsPasses() {
        PolicyEvaluationResult result = engine.evaluate(clean());

        assertThat(result.isDeclined()).isFalse();
        assertThat(result.isReferToManual()).isFalse();
        assertThat(result.getReasonCodes()).containsExactly("PASSED_AUTOMATED_POLICY");
    }

    @Test
    void declinesWhenAnnualRevenueIsBelowTheMinimum() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1002L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("100000.00"),
                new BigDecimal("15000.00"),
                6, 48, 720);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.isDeclined()).isTrue();
        assertThat(result.getReasonCodes()).contains("ANNUAL_REVENUE_BELOW_MINIMUM");
    }

    @Test
    void declinesWhenTimeInBusinessIsUnderTwentyFourMonths() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1003L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("250000.00"),
                new BigDecimal("40000.00"),
                6, 20, 720);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.isDeclined()).isTrue();
        assertThat(result.getReasonCodes()).contains("TIME_IN_BUSINESS_TOO_SHORT");
    }

    @Test
    void refersWhenThereIsNotEnoughStatementHistory() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1004L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("250000.00"),
                new BigDecimal("40000.00"),
                2, 48, 720);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.isReferToManual()).isTrue();
        assertThat(result.getReasonCodes()).contains("INSUFFICIENT_STATEMENT_HISTORY");
    }

    @Test
    void refersWhenTheAmountIsAboveTheProductCap() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1005L, "NSC_DIRECT", "SBA_7A", "NC",
                new BigDecimal("400000.00"),
                new BigDecimal("40000.00"),
                6, 48, 720);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.isReferToManual()).isTrue();
        assertThat(result.getReasonCodes()).contains("AMOUNT_ABOVE_PRODUCT_CAP");
    }

    @Test
    void refersWhenTheBureauReturnsNoHit() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1006L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("250000.00"),
                new BigDecimal("40000.00"),
                6, 48, null);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.isReferToManual()).isTrue();
        assertThat(result.getReasonCodes()).contains("CREDIT_BUREAU_NO_HIT");
    }

    @Test
    void refersCascadeLinesOfCreditInCalifornia() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1007L, "CASCADE", "LOC", "CA",
                new BigDecimal("100000.00"),
                new BigDecimal("40000.00"),
                6, 48, 720);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.getReasonCodes()).contains("CA_LOC_MANUAL_REVIEW_REQUIRED");
    }

    @Test
    void reasonCodesJoinIntoOneColumnValue() {
        PolicyEvaluationInput input = new PolicyEvaluationInput(
                1008L, "NSC_DIRECT", "TERM_LOAN", "NC",
                new BigDecimal("250000.00"),
                new BigDecimal("15000.00"),
                2, 20, 600);

        PolicyEvaluationResult result = engine.evaluate(input);

        assertThat(result.reasonCodesAsColumn())
                .isEqualTo("INSUFFICIENT_STATEMENT_HISTORY,TIME_IN_BUSINESS_TOO_SHORT,"
                        + "ANNUAL_REVENUE_BELOW_MINIMUM,OWNER_FICO_BELOW_MINIMUM");
    }
}
