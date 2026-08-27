package com.northstar.document.api;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicLong;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;

import com.northstar.document.entity.DocumentEntity;
import com.northstar.document.kafka.DocumentEventPublisher;
import com.northstar.document.repo.DocumentRepository;
import com.northstar.document.storage.ObjectStore;

class DocumentUploadControllerTest {

    private DocumentRepository documentRepository;
    private ObjectStore objectStore;
    private DocumentEventPublisher publisher;
    private DocumentUploadController controller;

    @BeforeEach
    void setUp() {
        documentRepository = mock(DocumentRepository.class);
        objectStore = mock(ObjectStore.class);
        publisher = mock(DocumentEventPublisher.class);
        controller = new DocumentUploadController(documentRepository, objectStore, publisher);

        AtomicLong ids = new AtomicLong(1);
        when(objectStore.put(anyLong(), anyString(), any())).thenReturn("northstar-documents/2026-05-01/1/abc.pdf");
        when(documentRepository.save(any(DocumentEntity.class))).thenAnswer(invocation -> {
            DocumentEntity saved = invocation.getArgument(0);
            saved.setDocumentId(ids.getAndIncrement());
            return saved;
        });
    }

    private MockMultipartFile statement() {
        return new MockMultipartFile("file", "may-statement.pdf", "application/pdf",
                "PDF BYTES FOR MAY".getBytes());
    }

    @Test
    void storesTheDocumentAndReturnsIt() throws IOException {
        var response = controller.upload(4021L, "BANK_STATEMENT", statement(), "NSC_DIRECT");

        assertThat(response.getStatusCode().value()).isEqualTo(201);
        assertThat(response.getBody()).containsEntry("applicationId", 4021L);
        assertThat(response.getBody()).containsEntry("status", "UPLOADED");
        assertThat(response.getBody().get("sha256")).isNotNull();
    }

    @Test
    void computesTheSameHashForTheSameBytes() {
        String first = DocumentUploadController.sha256Hex("PDF BYTES FOR MAY".getBytes());
        String second = DocumentUploadController.sha256Hex("PDF BYTES FOR MAY".getBytes());

        assertThat(first).isEqualTo(second).hasSize(64);
    }

    /**
     * Two identical uploads.
     *
     * <p>This is what happens today. Both calls save a row and both publish an event. The
     * API doc says the endpoint is idempotent. The test says it is not, and the test is the
     * one running in production.
     */
    @Test
    void twoIdenticalUploadsCreateTwoDocuments() throws IOException {
        controller.upload(4021L, "BANK_STATEMENT", statement(), "NSC_DIRECT");
        controller.upload(4021L, "BANK_STATEMENT", statement(), "NSC_DIRECT");

        verify(documentRepository, times(2)).save(any(DocumentEntity.class));
        verify(publisher, times(2)).publishUploaded(any());
    }

    @Test
    @Disabled("flaky, fix later. Passes on my machine and on Tomas's, fails on the CI box about "
            + "half the time with a MinIO connection reset. The stub container is probably not "
            + "up yet when this runs. bwilcox, 2024-04-30")
    void rejectsAFileLargerThanTheUploadLimit() throws IOException {
        byte[] big = new byte[30 * 1024 * 1024];
        MockMultipartFile huge = new MockMultipartFile("file", "huge.pdf", "application/pdf", big);

        var response = controller.upload(4021L, "BANK_STATEMENT", huge, "NSC_DIRECT");

        assertThat(response.getStatusCode().value()).isEqualTo(413);
    }
}
