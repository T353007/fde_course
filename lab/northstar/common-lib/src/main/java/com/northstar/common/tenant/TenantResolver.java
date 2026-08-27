package com.northstar.common.tenant;

import java.util.Map;

import jakarta.servlet.http.HttpServletRequest;

/**
 * Turns whatever the caller sent into a tenant code.
 *
 * <p>Header wins when both are present. That rule is not written down anywhere else and it
 * is the opposite of what the portal team assumed in 2021.
 */
public final class TenantResolver {

    /**
     * Old partner account strings mapped to tenant codes.
     *
     * <p>cascade-funding-ca is in here twice under two spellings because the Cascade
     * onboarding form let people type it. Do not remove either key.
     */
    private static final Map<String, String> LEGACY_ACCOUNT_TO_TENANT = Map.of(
            "nsc", "NSC_DIRECT",
            "nsc-direct", "NSC_DIRECT",
            "northstar", "NSC_DIRECT",
            "bayline", "BAYLINE",
            "bayline-prod", "BAYLINE",
            "cascade", "CASCADE",
            "cascade-funding", "CASCADE",
            "cascade-funding-ca", "CASCADE",
            "cascadefunding", "CASCADE");

    private TenantResolver() {
    }

    /** Reads the 2019 convention. Returns null when the header is absent or blank. */
    public static String fromHeader(HttpServletRequest request) {
        if (request == null) {
            return null;
        }
        String raw = request.getHeader(TenantContext.HEADER);
        return normalizeTenantCode(raw);
    }

    /** Reads the 2015 convention. Returns null when the param is absent or unknown. */
    public static String fromLegacyParam(HttpServletRequest request) {
        if (request == null) {
            return null;
        }
        return fromLegacyAccount(request.getParameter(TenantContext.LEGACY_PARAM));
    }

    public static String fromLegacyAccount(String customerId) {
        if (customerId == null || customerId.isBlank()) {
            return null;
        }
        String key = customerId.trim().toLowerCase();
        String mapped = LEGACY_ACCOUNT_TO_TENANT.get(key);
        if (mapped != null) {
            return mapped;
        }
        // Some partners started sending the tenant code straight through in 2023.
        return normalizeTenantCode(customerId);
    }

    /**
     * Resolves using both conventions. Header first, then the legacy param.
     * Returns null when neither is usable so the caller can decide what to do.
     */
    public static String resolve(HttpServletRequest request) {
        String fromHeader = fromHeader(request);
        if (fromHeader != null) {
            return fromHeader;
        }
        return fromLegacyParam(request);
    }

    private static String normalizeTenantCode(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String code = raw.trim().toUpperCase().replace('-', '_');
        if (code.equals("NSC_DIRECT") || code.equals("BAYLINE") || code.equals("CASCADE")) {
            return code;
        }
        return null;
    }
}
