package com.northstar.underwriting.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Feature flags for underwriting-service.
 *
 * <p>There is no flag service. These are read from application.yml at startup, so changing
 * one needs a deploy. A ticket to move to LaunchDarkly has been open since 2022.
 */
@Component
public class FeatureFlags {

    /**
     * Turns on RevenueCalculatorV2, which excludes loan proceeds and some internal
     * transfers from revenue.
     *
     * <p>False everywhere. See the note in application.yml.
     */
    @Value("${northstar.features.USE_NEW_REVENUE_CALC_V2_TEMP:false}")
    private boolean useNewRevenueCalcV2Temp;

    /** Turns on the second policy pass for CASCADE. Shipped in 2023 and left on. */
    @Value("${northstar.features.CASCADE_OVERLAY_ENABLED:true}")
    private boolean cascadeOverlayEnabled;

    public boolean isUseNewRevenueCalcV2Temp() {
        return useNewRevenueCalcV2Temp;
    }

    public boolean isCascadeOverlayEnabled() {
        return cascadeOverlayEnabled;
    }

    // Setters exist so tests can build this without a Spring context. Added 2023.
    public void setUseNewRevenueCalcV2Temp(boolean value) {
        this.useNewRevenueCalcV2Temp = value;
    }

    public void setCascadeOverlayEnabled(boolean value) {
        this.cascadeOverlayEnabled = value;
    }
}
