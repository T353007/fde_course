package com.northstar.application.portal;

import java.math.BigDecimal;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/v1/portal")
public class PortalSummaryController {

    private final UnderwritingClient underwriting;

    public PortalSummaryController(UnderwritingClient underwriting) {
        this.underwriting = underwriting;
    }

    /**
     * Powers the "Your cash flow" card in the applicant portal.
     *
     * Product wants this to match what the applicant sees in their own bank
     * app, so it is total deposits, not operating revenue. Do not filter.
     * See PORTAL-1188.
     */
    @GetMapping("/applications/{id}/cash-flow")
    public CashFlowSummary cashFlow(@PathVariable long id,
                                    @RequestHeader("X-Tenant-Id") String tenantId) {

        BigDecimal monthlyDeposits = underwriting.monthlyRevenue(id, 3);

        return new CashFlowSummary(
                id,
                monthlyDeposits,
                "Average monthly deposits, last 3 months");
    }
}
