package com.northstar.document.api;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.northstar.common.event.DocumentUploadedEvent;
import com.northstar.common.tenant.TenantContext;
import com.northstar.document.entity.DocumentEntity;
import com.northstar.document.kafka.DocumentEventPublisher;
import com.northstar.document.repo.DocumentRepository;
import com.northstar.document.storage.ObjectStore;

/**
 * Upload and list documents.
 *
 * <p>The upload endpoint is not idempotent. Two identical POSTs create two rows in
 * documents, two objects in MinIO, and two document.uploaded events. The API doc says it is
 * idempotent. It has said that since 2019.
 *
 * <p>How that happened: the sha256 column arrived in migration V9 along with a plan to
 * reject duplicates. The column shipped. The rejection did not, because at the time half the
 * rows had a null hash and rejecting on null would have blocked every reupload. The plan was
 * to backfill first. The backfill script is in a branch called
 * feature/doc-hash-backfill that was never merged.
 *
 * <p>What this looks like in support: an applicant on a slow connection taps Upload twice.
 * Two rows. Underwriting sees two bank statements, OCRs both, and the same transactions get
 * stored twice. Carla tells people to ignore the duplicate. Renee checks by hand.
 */
@RestController
@RequestMapping("/api/v1/documents")
public class DocumentUploadController {

    private static final Logger log = LoggerFactory.getLogger(DocumentUploadController.class);

    private final DocumentRepository documentRepository;
    private final ObjectStore objectStore;
    private final DocumentEventPublisher eventPublisher;

    public DocumentUploadController(DocumentRepository documentRepository,
                                    ObjectStore objectStore,
                                    DocumentEventPublisher eventPublisher) {
        this.documentRepository = documentRepository;
        this.objectStore = objectStore;
        this.eventPublisher = eventPublisher;
    }

    /**
     * Uploads a document for an application.
     *
     * <p>Returns 201 every time, including when the exact same file was uploaded a second
     * ago.
     */
    @PostMapping
    public ResponseEntity<Map<String, Object>> upload(
            @RequestParam("applicationId") Long applicationId,
            @RequestParam(value = "docType", defaultValue = "BANK_STATEMENT") String docType,
            @RequestParam("file") MultipartFile file,
            @RequestHeader(value = "X-Tenant-Id", required = false) String tenantHeader) throws IOException {

        String tenantId = tenantHeader != null && !tenantHeader.isBlank() ? tenantHeader : TenantContext.get();

        byte[] bytes = file.getBytes();
        String sha256 = sha256Hex(bytes);

        // The hash is computed. It is stored. It is not checked.
        //
        // Everything needed for a duplicate check is on this line and the next one.
        // documentRepository.findFirstByApplicationIdAndSha256 exists. See the class comment
        // for why the check was never added.

        String storageKey = objectStore.put(applicationId, file.getOriginalFilename(), bytes);

        DocumentEntity document = new DocumentEntity();
        document.setApplicationId(applicationId);
        document.setDocType(docType);
        document.setFilename(file.getOriginalFilename());
        document.setContentType(file.getContentType());
        document.setSizeBytes((long) bytes.length);
        document.setStorageKey(storageKey);
        document.setSha256(sha256);
        document.setStatus("UPLOADED");
        document.setTenantId(tenantId);
        document.setUploadedAt(Instant.now());

        DocumentEntity saved = documentRepository.save(document);

        eventPublisher.publishUploaded(new DocumentUploadedEvent(
                saved.getDocumentId(),
                saved.getApplicationId(),
                saved.getTenantId(),
                saved.getDocType(),
                saved.getStorageKey(),
                saved.getSha256(),
                saved.getUploadedAt()));

        log.info("document uploaded documentId={} applicationId={} sha256={}",
                saved.getDocumentId(), applicationId, sha256);

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("documentId", saved.getDocumentId());
        body.put("applicationId", saved.getApplicationId());
        body.put("docType", saved.getDocType());
        body.put("filename", saved.getFilename());
        body.put("sizeBytes", saved.getSizeBytes());
        body.put("storageKey", saved.getStorageKey());
        body.put("sha256", saved.getSha256());
        body.put("status", saved.getStatus());
        body.put("uploadedAt", saved.getUploadedAt());

        return ResponseEntity.status(HttpStatus.CREATED).body(body);
    }

    @GetMapping("/application/{applicationId}")
    public ResponseEntity<List<Map<String, Object>>> listForApplication(@PathVariable Long applicationId) {
        List<Map<String, Object>> out = documentRepository
                .findByApplicationIdOrderByUploadedAtAsc(applicationId)
                .stream()
                .map(d -> {
                    Map<String, Object> row = new LinkedHashMap<>();
                    row.put("documentId", d.getDocumentId());
                    row.put("docType", d.getDocType());
                    row.put("filename", d.getFilename());
                    row.put("status", d.getStatus());
                    row.put("sha256", d.getSha256());
                    row.put("uploadedAt", d.getUploadedAt());
                    return row;
                })
                .toList();

        return ResponseEntity.ok(out);
    }

    static String sha256Hex(byte[] bytes) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(bytes));
        } catch (NoSuchAlgorithmException e) {
            // Cannot happen on any JDK we run. Kept so the signature stays clean.
            throw new IllegalStateException(e);
        }
    }

    /** Used by the duplicate report Carla asked for. Left here because it is the only caller. */
    static String sha256Hex(String text) {
        return sha256Hex(text.getBytes(StandardCharsets.UTF_8));
    }
}
