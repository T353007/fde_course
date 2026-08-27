package com.northstar.underwriting.revenue;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.northstar.common.model.BankTransaction;

/**
 * Tests for the V2 calculator that is behind the flag.
 *
 * <p>These were written in 2021 while V2 was being built and never extended past the loan
 * exclusion. They pass. They also show exactly how far the work got.
 */
class RevenueCalculatorV2Test {

    private final RevenueCalculatorV2 calculator = new RevenueCalculatorV2(new InternalTransferDetector());

    private static BankTransaction txn(String date, String description, String amount) {
        return new BankTransaction(null, 1L, LocalDate.parse(date), description,
                new BigDecimal(amount), null, null);
    }

    @Test
    void excludesLoanProceeds() {
        List<BankTransaction> txns = List.of(
                txn("2026-05-04", "STRIPE PAYOUT", "48230.00"),
                txn("2026-05-18", "FASTCAPITAL LOAN", "75000.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 1))
                .isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void excludesInternalTransfersWhenTheBankFormatIsRecognized() {
        List<BankTransaction> txns = List.of(
                txn("2026-05-04", "STRIPE PAYOUT", "48230.00"),
                txn("2026-05-06", "TRANSFER FROM SAVINGS ****1221", "30000.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 1))
                .isEqualByComparingTo(new BigDecimal("48230.00"));
    }

    @Test
    void classifiesTheThreeCases() {
        assertThat(calculator.classify(txn("2026-05-18", "FASTCAPITAL LOAN", "75000.00")))
                .isEqualTo(RevenueCalculatorV2.ExclusionReason.LOAN_PROCEEDS);
        assertThat(calculator.classify(txn("2026-05-06", "XFER TO CHECKING ****0087", "5000.00")))
                .isEqualTo(RevenueCalculatorV2.ExclusionReason.INTERNAL_TRANSFER);
        assertThat(calculator.classify(txn("2026-05-04", "STRIPE PAYOUT", "48230.00")))
                .isEqualTo(RevenueCalculatorV2.ExclusionReason.NONE);
    }

    /**
     * The standard sample statement, run through V2.
     *
     * <p>V2 catches the Fastcapital loan and misses the transfer, because the sample file
     * does not print a masked account number on the transfer line. So the answer is 177,400
     * over three months instead of the 147,400 an underwriter would give you.
     */
    @Test
    void onlyGetsPartWayOnTheStandardSampleStatement() {
        List<BankTransaction> txns = List.of(
                txn("2026-05-04", "STRIPE PAYOUT", "48230.00"),
                txn("2026-05-06", "TRANSFER FROM SAVINGS", "30000.00"),
                txn("2026-05-11", "STRIPE PAYOUT", "51340.00"),
                txn("2026-05-18", "FASTCAPITAL LOAN", "75000.00"),
                txn("2026-05-22", "STRIPE PAYOUT", "47830.00"));

        assertThat(calculator.calculateMonthlyRevenue(txns, 3))
                .isEqualByComparingTo(new BigDecimal("59133.33"));
    }
}
