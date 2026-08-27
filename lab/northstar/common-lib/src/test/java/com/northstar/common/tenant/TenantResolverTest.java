package com.northstar.common.tenant;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;

class TenantResolverTest {

    @Test
    void readsTenantFromHeader() {
        MockHttpServletRequest req = new MockHttpServletRequest();
        req.addHeader(TenantContext.HEADER, "BAYLINE");

        assertThat(TenantResolver.resolve(req)).isEqualTo("BAYLINE");
    }

    @Test
    void readsTenantFromLegacyCustomerIdParam() {
        MockHttpServletRequest req = new MockHttpServletRequest();
        req.setParameter(TenantContext.LEGACY_PARAM, "bayline-prod");

        assertThat(TenantResolver.resolve(req)).isEqualTo("BAYLINE");
    }

    @Test
    void headerWinsWhenBothArePresent() {
        MockHttpServletRequest req = new MockHttpServletRequest();
        req.addHeader(TenantContext.HEADER, "CASCADE");
        req.setParameter(TenantContext.LEGACY_PARAM, "bayline-prod");

        assertThat(TenantResolver.resolve(req)).isEqualTo("CASCADE");
    }

    @Test
    void unknownTenantResolvesToNull() {
        MockHttpServletRequest req = new MockHttpServletRequest();
        req.addHeader(TenantContext.HEADER, "REDWOOD");

        assertThat(TenantResolver.resolve(req)).isNull();
    }

    @Test
    void contextFallsBackToNorthstarDirect() {
        TenantContext.clear();
        assertThat(TenantContext.get()).isEqualTo("NSC_DIRECT");
        assertThat(TenantContext.isSet()).isFalse();
    }
}
