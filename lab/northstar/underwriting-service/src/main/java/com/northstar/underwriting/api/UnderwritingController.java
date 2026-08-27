package com.northstar.underwriting.api;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.northstar.underwriting.decision.DecisionRequest;
import com.northstar.underwriting.decision.UnderwritingDecisionService;
import com.northstar.underwriting.entity.DecisionEntity;
import com.northstar.underwriting.repo.DecisionRepository;

/** Decision endpoints. */
@RestController
@RequestMapping("/api/v1/underwriting")
public class UnderwritingController {

    private final UnderwritingDecisionService decisionService;
    private final DecisionRepository decisionRepository;

    public UnderwritingController(UnderwritingDecisionService decisionService,
                                  DecisionRepository decisionRepository) {
        this.decisionService = decisionService;
        this.decisionRepository = decisionRepository;
    }

    /**
     * Runs the automated policy pass and writes a decision row.
     *
     * <p>Not idempotent. Calling it twice writes two decision rows. That is on purpose here,
     * because underwriters rerun a file after a document arrives and they want both records.
     */
    @PostMapping("/decisions")
    public ResponseEntity<Map<String, Object>> decide(@RequestBody DecisionRequest request) {
        DecisionEntity decision = decisionService.decide(request);
        return ResponseEntity.ok(toResponse(decision));
    }

    @GetMapping("/applications/{applicationId}/decision")
    public ResponseEntity<Map<String, Object>> latestDecision(@PathVariable Long applicationId) {
        return decisionRepository.findFirstByApplicationIdOrderByCreatedAtDesc(applicationId)
                .map(d -> ResponseEntity.ok(toResponse(d)))
                .orElseGet(() -> ResponseEntity.notFound().build());
    }

    /**
     * Builds the response by hand.
     *
     * <p>A LinkedHashMap instead of a DTO, so field order matches what the old portal
     * expected. The portal does not care about field order anymore. This has not changed.
     */
    private Map<String, Object> toResponse(DecisionEntity d) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("applicationId", d.getApplicationId());
        body.put("decisionId", d.getDecisionId());
        body.put("outcome", d.getOutcome());
        body.put("reasonCodes", d.getReasonCodes());
        body.put("monthlyRevenue", d.getMonthlyRevenue());
        body.put("dscr", d.getDscr());
        body.put("decidedBy", d.getDecidedBy());
        body.put("createdAt", d.getCreatedAt());
        return body;
    }
}
