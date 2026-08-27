package com.northstar.underwriting.revenue;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.stereotype.Component;

import com.northstar.common.model.BankTransaction;

/**
 * Tries to spot money moving between two accounts the applicant already owns.
 *
 * <p>An internal transfer is not revenue. The applicant moved 30,000 from savings to
 * checking and nothing was earned. Renee catches these by eye in about two seconds. This
 * class was the attempt to do it in code.
 *
 * <p>Status: unfinished. It only understands First Carolina Bank statements, because that
 * was the first sample file on hand. First Carolina always prints the other account as a
 * masked number at the end of the line, which makes the pattern easy. Nobody else does
 * that. Truist and Wells put the account somewhere else or leave it off. So for every other
 * bank this returns false, which means "not a transfer", which means the transfer gets
 * counted as revenue.
 *
 * <p>Started by dpatel in March 2021 during the V2 work. Last commit on this file is
 * 2021-04-02.
 */
@Component
public class InternalTransferDetector {

    /**
     * First Carolina internal transfer lines. Real examples from the sample file:
     *
     * <pre>
     *   TRANSFER FROM SAVINGS ****1221
     *   XFER TO CHECKING ****0087
     *   TRANSFER FROM MMKT ***4410
     * </pre>
     *
     * The masked account at the end is what makes it safe to call this a transfer. Without
     * it, "TRANSFER FROM SAVINGS" could be a wire from a customer named Savings Group LLC.
     * That actually happened in 2020 and it is why the mask is required.
     */
    private static final Pattern FIRST_CAROLINA_TRANSFER = Pattern.compile(
            "^\\s*(TRANSFER|XFER)\\s+(FROM|TO)\\s+(SAVINGS|SAV|CHECKING|CHK|MMKT|MONEY\\s+MARKET)\\s+\\*{2,4}\\d{4}\\s*$",
            Pattern.CASE_INSENSITIVE);

    /** Banks we know how to read. There is one. */
    public enum StatementFormat {
        FIRST_CAROLINA,
        UNKNOWN
    }

    public boolean isInternalTransfer(BankTransaction txn) {
        if (txn == null || txn.description() == null) {
            return false;
        }
        return isInternalTransfer(txn.description());
    }

    public boolean isInternalTransfer(String description) {
        if (description == null || description.isBlank()) {
            return false;
        }

        StatementFormat format = detectFormat(description);

        return switch (format) {
            case FIRST_CAROLINA -> matchesFirstCarolina(description);

            // ---------------------------------------------------------------------
            // This is where the work stopped.
            //
            // Truist prints internal transfers as:
            //     ONLINE TRANSFER REF #IB0K3MQP2X FROM SAVINGS
            // and Wells prints them as:
            //     ONLINE TRANSFER FROM BUSINESS MARKET RATE SAVINGS XXXXXX1221
            //
            // Neither has the trailing mask in the same position, and the Wells one uses X
            // instead of an asterisk. Matching those needs a per bank parser, which needs
            // the bank name, which is not on the transaction row. It is on the document, and
            // document-service does not pass it through.
            //
            // Blocked on that. Ask Sam whether document_extractions can carry the
            // institution name. dpatel, 2021-04-02.
            // ---------------------------------------------------------------------
            case UNKNOWN -> false;
        };
    }

    /**
     * Guesses which bank printed this line.
     *
     * <p>The guess is only ever FIRST_CAROLINA or UNKNOWN, because the shape of the First
     * Carolina line is the only shape we recognize. This is circular and we knew it. The
     * plan was to replace it once the institution name was available.
     */
    public StatementFormat detectFormat(String description) {
        if (description == null) {
            return StatementFormat.UNKNOWN;
        }
        if (FIRST_CAROLINA_TRANSFER.matcher(description).matches()) {
            return StatementFormat.FIRST_CAROLINA;
        }
        return StatementFormat.UNKNOWN;
    }

    private boolean matchesFirstCarolina(String description) {
        Matcher m = FIRST_CAROLINA_TRANSFER.matcher(description);
        return m.matches();
    }

    /**
     * Truist support. Not implemented.
     *
     * <p>Left in place so the next person can see what the shape was supposed to be. It
     * always returns false today.
     */
    @SuppressWarnings("unused")
    private boolean matchesTruistFormat(String description) {
        // TODO(dpatel, 2021-04): needs the reference number stripped first, then the
        // account name matched against the applicant's own account list, which we do not
        // store. Do not turn this on until that list exists.
        return false;
    }
}
