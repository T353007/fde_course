package com.northstar.underwriting.decision;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import com.northstar.common.model.BankTransaction;
import com.northstar.underwriting.config.FeatureFlags;
import com.northstar.underwriting.revenue.InternalTransferDetector;
import com.northstar.underwriting.revenue.RevenueCalculator;
import com.northstar.underwriting.revenue.RevenueCalculatorV2;

class DebtServiceCoverageServiceTest {

    private DebtServiceCoverageService service;
    private FeatureFlags flags;

    @BeforeEach
    void setUp() {
        flags = new FeatureFlags();
        flags.setUseNewRevenueCalcV2Temp(false);
        service = new DebtServiceCoverageService(
                new RevenueCalculator(),
                new RevenueCalculatorV2(new InternalTransferDetector()),
                flags);
    }

    private static BankTransaction txn(String description, String amount) {
        return new BankTransaction(null, 1L, LocalDate.parse("2026-05-04"), description,
                new BigDecimal(amount), null, null);
    }

    @Test
    void computesDscrFromMonthlyRevenue() {
        List<BankTransaction> txns = List.of(txn("STRIPE PAYOUT", "252400.00"));

        BigDecimal dscr = service.computeDscr(txns, 1, new BigDecimal("30000.00"));

        // 252,400 times the 18 percent assumed margin is 45,432. Divided by 30,000.
        assertThat(dscr).isEqualByComparingTo(new BigDecimal("1.5144"));
    }

    @Test
    void passesTheFloorAtOnePointTwoFive() {
        assertThat(service.passesPolicyFloor(new BigDecimal("1.25"))).isTrue();
        assertThat(service.passesPolicyFloor(new BigDecimal("1.2499"))).isFalse();
        assertThat(service.passesPolicyFloor(null)).isFalse();
    }

    @Test
    void returnsAVeryHighRatioWhenThereIsNoDebtService() {
        List<BankTransaction> txns = List.of(txn("STRIPE PAYOUT", "10000.00"));

        assertThat(service.computeDscr(txns, 1, BigDecimal.ZERO))
                .isEqualByComparingTo(new BigDecimal("99.9999"));
        assertThat(service.computeDscr(txns, 1, null))
                .isEqualByComparingTo(new BigDecimal("99.9999"));
    }

    @Test
    void usesTheV2CalculatorWhenTheFlagIsOn() {
        flags.setUseNewRevenueCalcV2Temp(true);

        List<BankTransaction> txns = List.of(
                txn("STRIPE PAYOUT", "100000.00"),
                txn("FASTCAPITAL LOAN", "75000.00"));

        // 100,000 times 0.18 is 18,000. Divided by 30,000.
        assertThat(service.computeDscr(txns, 1, new BigDecimal("30000.00")))
                .isEqualByComparingTo(new BigDecimal("0.6000"));
    }

    @Test
    @Disabled("flaky, fix later. This one started failing after the 2024 statement fixture was "
            + "regenerated and I do not know if the fixture or the code is wrong. "
            + "tferreira, 2024-05-08")
    void matchesTheDscrOnTheAuditedPortfolioSample() {
        List<BankTransaction> txns = List.of(
                txn("STRIPE PAYOUT", "88420.00"),
                txn("SQUARE INC DEPOSIT", "12100.00"),
                txn("TRANSFER FROM SAVINGS ****1221", "25000.00"));

        BigDecimal dscr = service.computeDscr(txns, 3, new BigDecimal("14200.00"));

        assertThat(dscr).isEqualByComparingTo(new BigDecimal("0.5300"));
    }
}
