package com.northstar.common.dto;

import java.math.BigDecimal;

/**
 * What underwriting-service returns for the revenue endpoint.
 *
 * <p>The field is called monthlyRevenue here. The portal DTO calls the same number
 * avgMonthlyRevenue and the application summary DTO calls it revenue. There was a ticket
 * to unify these three (PLAT-2211). It was closed as won't fix in 2022 because the
 * reviewer portal, the CRM sync job, and a Looker dashboard all read the old names.
 */
public class UnderwritingRevenueView {

    private Long applicationId;
    private BigDecimal monthlyRevenue;
    private int monthsOfHistory;

    /** OPERATING or TOTAL_CREDITS. Set from a constant, so it always says the same thing. */
    private String basis;

    public UnderwritingRevenueView() {
    }

    public UnderwritingRevenueView(Long applicationId, BigDecimal monthlyRevenue, int monthsOfHistory, String basis) {
        this.applicationId = applicationId;
        this.monthlyRevenue = monthlyRevenue;
        this.monthsOfHistory = monthsOfHistory;
        this.basis = basis;
    }

    public Long getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(Long applicationId) {
        this.applicationId = applicationId;
    }

    public BigDecimal getMonthlyRevenue() {
        return monthlyRevenue;
    }

    public void setMonthlyRevenue(BigDecimal monthlyRevenue) {
        this.monthlyRevenue = monthlyRevenue;
    }

    public int getMonthsOfHistory() {
        return monthsOfHistory;
    }

    public void setMonthsOfHistory(int monthsOfHistory) {
        this.monthsOfHistory = monthsOfHistory;
    }

    public String getBasis() {
        return basis;
    }

    public void setBasis(String basis) {
        this.basis = basis;
    }
}
