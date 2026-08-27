package com.northstar.common.tenant;

/**
 * Holds the tenant for the current request.
 *
 * <p>There are two ways a tenant arrives at a Northstar service and both are live.
 *
 * <ul>
 *   <li>The X-Tenant-Id header. This is the 2019 convention. underwriting-service,
 *       document-service, and fraud-service use it.
 *   <li>A customer_id request parameter. This is the 2015 convention from the original
 *       portal. application-service still accepts it because the partner brands send it
 *       and Bayline has never agreed to a change window.
 * </ul>
 *
 * <p>The values are not the same shape either. The header carries a tenant code like
 * NSC_DIRECT. The param carries a partner account string like bayline-prod, which has to
 * be mapped. See {@link TenantResolver}.
 */
public final class TenantContext {

    public static final String HEADER = "X-Tenant-Id";
    public static final String LEGACY_PARAM = "customer_id";

    /** Used when nothing was supplied. Yes, this means unknown traffic reads as Northstar direct. */
    public static final String DEFAULT_TENANT = "NSC_DIRECT";

    private static final ThreadLocal<String> CURRENT = new ThreadLocal<>();

    private TenantContext() {
    }

    public static void set(String tenantId) {
        CURRENT.set(tenantId);
    }

    /**
     * Returns the tenant for this thread, or NSC_DIRECT if none was set.
     *
     * <p>The fallback is the reason a Bayline request with a missing param can read
     * Northstar direct config. It has not caused a data leak that we know of, because the
     * repositories filter on tenant_id from the entity, not from here. That is luck, not
     * design.
     */
    public static String get() {
        String v = CURRENT.get();
        return v == null ? DEFAULT_TENANT : v;
    }

    public static boolean isSet() {
        return CURRENT.get() != null;
    }

    public static void clear() {
        CURRENT.remove();
    }
}
