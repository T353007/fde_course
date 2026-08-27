package com.northstar.document.ocr;

import java.math.BigDecimal;

/**
 * Turns whatever OptiScan calls an amount into a BigDecimal.
 *
 * <p>Handles the formats we have actually seen. Returns null when it cannot, and the caller
 * drops the line. Dropping a line silently is not great. It is better than storing a wrong
 * number, which is what the previous version did by calling replaceAll on commas and
 * hoping.
 */
public final class AmountParser {

    private AmountParser() {
    }

    public static BigDecimal parse(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }

        String cleaned = raw.trim()
                .replace("$", "")
                .replace(" ", "")
                .replace("\u00a0", "");

        boolean negative = false;

        // Some statements wrap debits in parentheses.
        if (cleaned.startsWith("(") && cleaned.endsWith(")")) {
            negative = true;
            cleaned = cleaned.substring(1, cleaned.length() - 1);
        }
        if (cleaned.startsWith("-")) {
            negative = true;
            cleaned = cleaned.substring(1);
        }
        if (cleaned.startsWith("+")) {
            cleaned = cleaned.substring(1);
        }

        cleaned = normalizeSeparators(cleaned);

        try {
            BigDecimal value = new BigDecimal(cleaned);
            return negative ? value.negate() : value;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    /**
     * Works out which character is the decimal point.
     *
     * <p>European formatting shows up on faxed statements that were scanned abroad. If the
     * last separator is a comma with exactly two digits after it, treat the comma as the
     * decimal point.
     */
    private static String normalizeSeparators(String value) {
        int lastComma = value.lastIndexOf(',');
        int lastDot = value.lastIndexOf('.');

        if (lastComma > lastDot && value.length() - lastComma == 3) {
            return value.replace(".", "").replace(',', '.');
        }
        return value.replace(",", "");
    }
}
