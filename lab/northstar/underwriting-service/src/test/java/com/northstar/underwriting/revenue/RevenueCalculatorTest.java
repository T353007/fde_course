package com.northstar.underwriting.revenue;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import com.northstar.common.model.BankTransaction;

/**
 * Tests for RevenueCalculator.
 *
 * <p>Covers the arithmetic. Does not cover what should count as revenue, because that was
 * never decided. See the TODO in the class under test.
 */
class RevenueCalculatorTest {

    private final RevenueCalculator calculator = new RevenueCalculator();

    private static BankTransaction txn(String date, String description, String amount) {
        return new BankTransaction(null, 1L, LocalDate.parse(date), description,
                new BigDecimal(amount), null, null);
    }

    @Test
    void returnsZeroForNoTransactions() {
        assertThat(calculator.calculateMonthlyRevenue(List.of(), 3))
                .isEqualByComparingTo(BigDecimal.ZERO);
    }

    @Test
    void returnsZeroWhenMonthsIsZero() {
        List<BankTransaction> txns = List.of(txn("2026-05-04", "STRIPE PAYOUT", "48230.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 0))
                .isEqualByComparingTo(BigDecimal.ZERO);
    }

    @Test
    void returnsZeroWhenMonthsIsNegative() {
        List<BankTransaction> txns = List.of(txn("2026-05-04", "STRIPE PAYOUT", "48230.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, -1))
                .isEqualByComparingTo(BigDecimal.ZERO);
    }

    @Test
    void ignoresDebits() {
        List<BankTransaction> txns = List.of(
                txn("2026-05-04", "STRIPE PAYOUT", "30000.00"),
                txn("2026-05-05", "RENT PAYMENT", "-8000.00"),
                txn("2026-05-06", "PAYROLL", "-12000.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 1))
                .isEqualByComparingTo(new BigDecimal("30000.00"));
    }

    @Test
    void dividesByTheNumberOfMonths() {
        List<BankTransaction> txns = List.of(
                txn("2026-03-04", "STRIPE PAYOUT", "30000.00"),
                txn("2026-04-04", "STRIPE PAYOUT", "30000.00"),
                txn("2026-05-04", "STRIPE PAYOUT", "30000.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 3))
                .isEqualByComparingTo(new BigDecimal("30000.00"));
    }

    @Test
    void roundsToTwoDecimalPlaces() {
        List<BankTransaction> txns = List.of(txn("2026-05-04", "STRIPE PAYOUT", "100.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 3))
                .isEqualByComparingTo(new BigDecimal("33.33"));
    }

    /**
     * The standard three month sample file.
     *
     * <p>This is the file support and QA both use when they need a known application. The
     * expected number here matches what the portal shows and what the last audit signed
     * off on, so it is the number to hold the calculator to.
     */
    @Test
    void calculatesAverageMonthlyRevenueForTheStandardSampleStatement() {
        List<BankTransaction> txns = List.of(
                txn("2026-05-04", "STRIPE PAYOUT", "48230.00"),
                txn("2026-05-06", "TRANSFER FROM SAVINGS", "30000.00"),
                txn("2026-05-11", "STRIPE PAYOUT", "51340.00"),
                txn("2026-05-18", "FASTCAPITAL LOAN", "75000.00"),
                txn("2026-05-22", "STRIPE PAYOUT", "47830.00"));

        BigDecimal result = calculator.calculateMonthlyRevenue(txns, 3);

        // 252,400 in total credits over three months.
        assertThat(result).isEqualByComparingTo(new BigDecimal("84133.33"));
    }

    @Test
    @Disabled("flaky, fix later. Fails about one run in six on CI, passes locally every time. "
            + "Suspect the BigDecimal scale on the divide but have not proven it. jkowalski, 2024-02-19")
    void handlesFiftyThousandTransactionsWithoutPrecisionLoss() {
        List<BankTransaction> txns = new java.util.ArrayList<>();
        for (int i = 0; i < 50_000; i++) {
            txns.add(txn("2026-05-04", "CARD SETTLEMENT " + i, "13.37"));
        }

        BigDecimal result = calculator.calculateMonthlyRevenue(txns, 3);

        assertThat(result).isEqualByComparingTo(new BigDecimal("222833.33"));
    }
}
