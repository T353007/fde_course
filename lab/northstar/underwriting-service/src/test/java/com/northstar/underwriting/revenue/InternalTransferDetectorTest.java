package com.northstar.underwriting.revenue;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class InternalTransferDetectorTest {

    private final InternalTransferDetector detector = new InternalTransferDetector();

    @Test
    void detectsFirstCarolinaTransferLines() {
        assertThat(detector.isInternalTransfer("TRANSFER FROM SAVINGS ****1221")).isTrue();
        assertThat(detector.isInternalTransfer("XFER TO CHECKING ****0087")).isTrue();
        assertThat(detector.isInternalTransfer("TRANSFER FROM MMKT ***4410")).isTrue();
    }

    @Test
    void doesNotFlagOrdinaryDeposits() {
        assertThat(detector.isInternalTransfer("STRIPE PAYOUT")).isFalse();
        assertThat(detector.isInternalTransfer("SQUARE INC DEPOSIT")).isFalse();
    }

    @Test
    void doesNotFlagAWireFromACompanyWithSavingsInTheName() {
        assertThat(detector.isInternalTransfer("WIRE FROM SAVINGS GROUP LLC")).isFalse();
    }

    /**
     * Documents what this class does today, not what it should do.
     *
     * <p>A transfer with no masked account number is not detected. That is most banks. The
     * detector was only ever finished for First Carolina statements.
     */
    @Test
    void missesTransfersFromEveryOtherBankFormat() {
        assertThat(detector.isInternalTransfer("TRANSFER FROM SAVINGS")).isFalse();
        assertThat(detector.isInternalTransfer("ONLINE TRANSFER REF #IB0K3MQP2X FROM SAVINGS")).isFalse();
        assertThat(detector.isInternalTransfer(
                "ONLINE TRANSFER FROM BUSINESS MARKET RATE SAVINGS XXXXXX1221")).isFalse();
    }

    @Test
    void handlesNullAndBlank() {
        assertThat(detector.isInternalTransfer((String) null)).isFalse();
        assertThat(detector.isInternalTransfer("   ")).isFalse();
    }
}
