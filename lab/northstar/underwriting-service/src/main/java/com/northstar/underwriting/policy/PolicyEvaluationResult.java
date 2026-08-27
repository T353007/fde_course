package com.northstar.underwriting.policy;

import java.util.ArrayList;
import java.util.List;

/**
 * Result of a policy pass.
 *
 * <p>Reason codes are collected in the order the rules ran. The order matters to the
 * adverse action letter, because the letter template prints the first three. So a rule
 * added at the bottom of the list can never appear on a letter.
 */
public class PolicyEvaluationResult {

    private final List<String> reasonCodes = new ArrayList<>();
    private boolean declined;
    private boolean referToManual;

    public void decline(String reasonCode) {
        this.declined = true;
        this.reasonCodes.add(reasonCode);
    }

    public void refer(String reasonCode) {
        this.referToManual = true;
        this.reasonCodes.add(reasonCode);
    }

    public void note(String reasonCode) {
        this.reasonCodes.add(reasonCode);
    }

    public boolean isDeclined() {
        return declined;
    }

    public boolean isReferToManual() {
        return referToManual;
    }

    public List<String> getReasonCodes() {
        return List.copyOf(reasonCodes);
    }

    /** The decisions table stores this as one comma separated string. */
    public String reasonCodesAsColumn() {
        return String.join(",", reasonCodes);
    }
}
