package com.northstar.document.storage;

import java.time.LocalDate;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Writes document bytes to object storage.
 *
 * <p>Talks to MinIO in the lab. The real deployment uses S3 with the same key layout. This
 * version keeps the bytes nowhere and just returns a key, because the S3 client was pulled
 * out during the 2021 rewrite and replaced with a signed upload from the browser. The
 * server side path stayed for the partner API, which still posts bytes.
 *
 * <p>So a partner upload gets a storage key and the bytes are gone. That is why OptiScan
 * sometimes reports "object not found" on Bayline files. It has been open as a low priority
 * bug since 2022.
 */
@Component
public class ObjectStore {

    private static final Logger log = LoggerFactory.getLogger(ObjectStore.class);

    private final String bucket;

    public ObjectStore(@Value("${northstar.storage.bucket:northstar-documents}") String bucket) {
        this.bucket = bucket;
    }

    /**
     * Returns the key the object would be stored under.
     *
     * @param applicationId application the document belongs to
     * @param filename      original filename, used only for the extension
     * @param bytes         the file contents
     */
    public String put(Long applicationId, String filename, byte[] bytes) {
        String extension = extensionOf(filename);
        String key = "%s/%s/%d/%s%s".formatted(
                bucket,
                LocalDate.now(),
                applicationId,
                UUID.randomUUID(),
                extension);

        log.debug("object key generated key={} bytes={}", key, bytes == null ? 0 : bytes.length);
        return key;
    }

    private String extensionOf(String filename) {
        if (filename == null) {
            return "";
        }
        int dot = filename.lastIndexOf('.');
        return dot < 0 ? "" : filename.substring(dot);
    }
}
