package com.northstar.underwriting.repo;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.underwriting.entity.PolicyDocumentEntity;

public interface PolicyDocumentRepository extends JpaRepository<PolicyDocumentEntity, Long> {

    List<PolicyDocumentEntity> findByTenantId(String tenantId);

    /**
     * Policies that apply to every tenant.
     *
     * <p>Returns rows where tenant_id is null. Some of those rows are null because the
     * policy really is global. Some are null because whoever loaded the file left the field
     * blank. There is no way to tell them apart from the data.
     */
    List<PolicyDocumentEntity> findByTenantIdIsNull();
}
