package com.northstar.document.repo;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.northstar.document.entity.DocumentEntity;

public interface DocumentRepository extends JpaRepository<DocumentEntity, Long> {

    List<DocumentEntity> findByApplicationIdOrderByUploadedAtAsc(Long applicationId);

    /**
     * Finds a document by hash inside one application.
     *
     * <p>This method exists and works. The upload path does not call it. It was added in
     * 2021 for a duplicate report that Carla asked for, and the report is the only caller.
     */
    Optional<DocumentEntity> findFirstByApplicationIdAndSha256(Long applicationId, String sha256);
}
