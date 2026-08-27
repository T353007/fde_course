package com.northstar.application.portal;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;

import org.junit.jupiter.api.Test;

class PortalSummaryControllerTest {

    @Test
    void asksUnderwritingForThreeMonthsAndDoesNotFilter() {
        UnderwritingClient client = mock(UnderwritingClient.class);
        when(client.monthlyRevenue(10241L, 3)).thenReturn(new BigDecimal("84133.33"));

        PortalSummaryController controller = new PortalSummaryController(client);
        CashFlowSummary summary = controller.cashFlow(10241L, "NSC_DIRECT");

        assertThat(summary.monthlyDeposits()).isEqualByComparingTo(new BigDecimal("84133.33"));
        assertThat(summary.label()).contains("deposits");
        verify(client).monthlyRevenue(10241L, 3);
    }
}
