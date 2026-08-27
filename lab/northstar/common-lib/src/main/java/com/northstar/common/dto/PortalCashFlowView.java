package com.northstar.common.dto;

import java.math.BigDecimal;

/**
 * The cash flow widget the applicant sees in the portal.
 *
 * <p>Field name is avgMonthlyRevenue. It holds the same number underwriting-service calls
 * monthlyRevenue. Wendy's team picked this name in 2020 and the portal build has it baked
 * into a TypeScript type, so renaming it breaks the front end.
 */
public class PortalCashFlowView {

    private Long applicationId;
    private BigDecimal avgMonthlyRevenue;
    private BigDecimal totalDeposits;
    private int monthsOfHistory;

    public PortalCashFlowView() {
    }

    public Long getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(Long applicationId) {
        this.applicationId = applicationId;
    }

    public BigDecimal getAvgMonthlyRevenue() {
        return avgMonthlyRevenue;
    }

    public void setAvgMonthlyRevenue(BigDecimal avgMonthlyRevenue) {
        this.avgMonthlyRevenue = avgMonthlyRevenue;
    }

    public BigDecimal getTotalDeposits() {
        return totalDeposits;
    }

    public void setTotalDeposits(BigDecimal totalDeposits) {
        this.totalDeposits = totalDeposits;
    }

    public int getMonthsOfHistory() {
        return monthsOfHistory;
    }

    public void setMonthsOfHistory(int monthsOfHistory) {
        this.monthsOfHistory = monthsOfHistory;
    }
}
