package com.northstar.fraud.scoring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.northstar.common.dto.FraudScoreRequest;
import com.northstar.common.dto.FraudScoreResponse;
import com.northstar.fraud.vendor.SentinelRiskClient;
import com.northstar.fraud.vendor.SentinelRiskClient.SentinelScore;

@ExtendWith(MockitoExtension.class)
class FraudScoringServiceTest {

    @Mock
    SentinelRiskClient sentinel;

    @Test
    void mapsVendorScoreAndKeepsReasonCodes() {
        when(sentinel.fetch(any(), any()))
                .thenReturn(new SentinelScore(720, List.of("DEVICE_MISMATCH"), false));

        FraudScoringService service = new FraudScoringService(sentinel);
        FraudScoreResponse response = service.score(new FraudScoreRequest(
                12L, "NSC_DIRECT", "Corner Rise Bakery LLC", "12-3456789",
                "1221", "owner@bakery.test", null, null));

        assertThat(response.score()).isEqualTo(720);
        assertThat(response.riskBand()).isEqualTo("REVIEW");
        assertThat(response.reasonCodes()).contains("DEVICE_MISMATCH");
        assertThat(response.vendorDegraded()).isFalse();
        assertThat(response.isBlocking()).isTrue();
    }

    @Test
    void marksDegradedWhenVendorReturnsBareScore() {
        when(sentinel.fetch(any(), any()))
                .thenReturn(new SentinelScore(100, List.of(), true));

        FraudScoringService service = new FraudScoringService(sentinel);
        FraudScoreResponse response = service.score(new FraudScoreRequest(
                13L, "NSC_DIRECT", "Acme", "99-1111111", null, "ok@acme.test", null, null));

        assertThat(response.vendorDegraded()).isTrue();
        assertThat(response.reasonCodes()).contains("VENDOR_DEGRADED");
    }

    @Test
    void bandBoundaries() {
        assertThat(FraudScoringService.bandFor(0)).isEqualTo("LOW");
        assertThat(FraudScoringService.bandFor(350)).isEqualTo("MEDIUM");
        assertThat(FraudScoringService.bandFor(600)).isEqualTo("REVIEW");
        assertThat(FraudScoringService.bandFor(800)).isEqualTo("HIGH");
    }
}
