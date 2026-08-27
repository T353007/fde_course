package com.northstar.fraud.api;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.northstar.common.dto.FraudScoreRequest;
import com.northstar.common.dto.FraudScoreResponse;
import com.northstar.fraud.scoring.FraudScoringService;

@RestController
@RequestMapping("/api/v1/fraud")
public class FraudScoreController {

    private final FraudScoringService scoringService;

    public FraudScoreController(FraudScoringService scoringService) {
        this.scoringService = scoringService;
    }

    @PostMapping("/score")
    public ResponseEntity<FraudScoreResponse> score(@RequestBody FraudScoreRequest request) {
        return ResponseEntity.ok(scoringService.score(request));
    }
}
