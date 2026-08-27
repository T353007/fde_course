package com.northstar.common.model;

import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * One line off a bank statement.
 *
 * <p>This was a plain old Java bean until 2023, when it became a record. The old bean had
 * setters and half the code mutated the category in place. Two of those call sites still
 * exist and now build a new record instead. Search for withCategory if you are looking
 * for them.
 *
 * <p>category is null for anything we have not classified yet, which is most rows before
 * 2024. categorySource tells you who set the category. It was added in migration V12 and
 * is null on every row loaded before that.
 */
public record BankTransaction(
        Long id,
        Long applicationId,
        LocalDate postedDate,
        String description,
        BigDecimal amount,
        String category,
        String categorySource) {

    /** Values we actually see in category_source. There is no enum because V12 shipped in a hurry. */
    public static final String SOURCE_OPTISCAN = "OPTISCAN";
    public static final String SOURCE_RULES = "RULES_ENGINE";
    public static final String SOURCE_MANUAL = "UNDERWRITER";

    public BankTransaction withCategory(String newCategory, String source) {
        return new BankTransaction(id, applicationId, postedDate, description, amount, newCategory, source);
    }

    /** True when money came in. Debits are stored as negative numbers. Usually. */
    public boolean isCredit() {
        return amount != null && amount.signum() > 0;
    }
}
