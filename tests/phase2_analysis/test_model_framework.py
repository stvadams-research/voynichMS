from phase2_analysis.models.disconfirmation import DisconfirmationEngine, PerturbationConfig
from phase2_analysis.models.evaluation import CrossModelEvaluator
from phase2_analysis.models.interface import (
    DisconfirmationResult,
    ExplicitModel,
    ModelPrediction,
    ModelStatus,
    PredictionType,
)
from phase2_analysis.models.registry import ModelRegistry


class DummyModel(ExplicitModel):
    def __init__(
        self,
        store,
        model_id: str,
        explanation_class: str = "constructed_system",
        prediction_outcomes: dict | None = None,
        degradation_score: float = 0.1,
        reported_survives: bool = True,
        rule_count: int = 3,
        failure_count: int = 2,
    ):
        super().__init__(store)
        self._model_id = model_id
        self._explanation_class = explanation_class
        self._prediction_outcomes = prediction_outcomes or {"p1": True, "p2": True}
        self._degradation_score = degradation_score
        self._reported_survives = reported_survives
        self._rules = [f"R{i}" for i in range(rule_count)]
        self._failure_conditions = [f"F{i}" for i in range(failure_count)]
        self._predictions = [
            ModelPrediction(
                prediction_id=pid,
                prediction_type=PredictionType.STRUCTURAL,
                description=f"Prediction {pid}",
                test_method="dummy",
                success_criterion="true",
                failure_criterion="false",
            )
            for pid in self._prediction_outcomes
        ]

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_name(self) -> str:
        return f"Model {self._model_id}"

    @property
    def explanation_class(self) -> str:
        return self._explanation_class

    @property
    def description(self) -> str:
        return "Dummy model for framework testing."

    @property
    def rules(self) -> list[str]:
        return self._rules

    @property
    def failure_conditions(self) -> list[str]:
        return self._failure_conditions

    def get_predictions(self) -> list[ModelPrediction]:
        return self._predictions

    def test_prediction(self, prediction: ModelPrediction, dataset_id: str) -> ModelPrediction:
        prediction.tested = True
        prediction.passed = bool(self._prediction_outcomes[prediction.prediction_id])
        prediction.actual_result = f"{dataset_id}:{prediction.prediction_id}"
        prediction.confidence = 0.9 if prediction.passed else 0.4
        return prediction

    def apply_perturbation(
        self, perturbation_type: str, dataset_id: str, strength: float
    ) -> DisconfirmationResult:
        return DisconfirmationResult(
            model_id=self.model_id,
            test_id=f"{perturbation_type}_{strength:.2f}",
            perturbation_type=perturbation_type,
            survived=self._reported_survives,
            degradation_score=self._degradation_score,
            metrics={"dataset_id": dataset_id},
        )


def test_model_status_updates_from_prediction_outcomes():
    passing_model = DummyModel(
        store=None,
        model_id="pass_model",
        prediction_outcomes={"p1": True, "p2": True},
    )
    passing_model.test_all_predictions("voynich_real")
    assert passing_model.status == ModelStatus.SURVIVING

    failing_model = DummyModel(
        store=None,
        model_id="fail_model",
        prediction_outcomes={"p1": False, "p2": False},
    )
    failing_model.test_all_predictions("voynich_real")
    assert failing_model.status == ModelStatus.FALSIFIED


def test_disconfirmation_engine_enforces_failure_threshold_and_stops_early():
    model = DummyModel(
        store=None,
        model_id="threshold_model",
        prediction_outcomes={"p1": True},
        degradation_score=0.95,
        reported_survives=True,
    )
    battery = [
        PerturbationConfig(
            perturbation_type="ordering",
            description="test battery",
            strength_levels=[0.1, 0.2],
            failure_threshold=0.6,
        )
    ]
    engine = DisconfirmationEngine(store=None, perturbation_battery=battery)
    results = engine.run_full_battery(model, "voynich_real")

    assert len(results) == 1
    assert results[0].survived is False
    assert model.status == ModelStatus.FALSIFIED

    log = engine.generate_disconfirmation_log(model)
    assert log["total_tests"] == 1
    assert log["total_failed"] == 1


def test_registry_and_cross_model_evaluator_generate_consistent_report():
    class ModelA(DummyModel):
        def __init__(self, store):
            super().__init__(
                store=store,
                model_id="model_a",
                explanation_class="visual_grammar",
                prediction_outcomes={"p1": True, "p2": True},
                degradation_score=0.10,
                rule_count=3,
                failure_count=3,
            )

    class ModelB(DummyModel):
        def __init__(self, store):
            super().__init__(
                store=store,
                model_id="model_b",
                explanation_class="constructed_system",
                prediction_outcomes={"p1": False, "p2": False},
                degradation_score=0.90,
                rule_count=8,
                failure_count=1,
            )

    registry = ModelRegistry(store=None)
    model_a = registry.register(ModelA)
    model_b = registry.register(ModelB)

    model_a.test_all_predictions("voynich_real")
    model_b.test_all_predictions("voynich_real")

    model_a.record_disconfirmation(
        DisconfirmationResult(
            model_id="model_a",
            test_id="t1",
            perturbation_type="ordering",
            survived=True,
            degradation_score=0.1,
        )
    )
    model_b.record_disconfirmation(
        DisconfirmationResult(
            model_id="model_b",
            test_id="t1",
            perturbation_type="ordering",
            survived=False,
            degradation_score=0.9,
            failure_mode="collapsed",
        )
    )

    evaluator = CrossModelEvaluator(registry.get_all())
    report = evaluator.generate_report()

    assert report["total_models"] == 2
    assert report["falsified_models"] >= 1
    assert report["overall_ranking"][0][0] == "model_a"
    assert set(report["all_scores"].keys()) == {"model_a", "model_b"}

    registry.discontinue("model_b", "manual decision")
    assert registry.get("model_b").status == ModelStatus.DISCONTINUED
