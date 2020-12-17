#  ------------------------------------------------------------------------------------------
#  Copyright (c) Microsoft Corporation. All rights reserved.
#  Licensed under the MIT License (MIT). See LICENSE in the repo root for license information.
#  ------------------------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import List

import pytest

from InnerEye.Common.common_util import logging_to_stdout
from InnerEye.Common.metrics_dict import MetricType, MetricsDict
from InnerEye.Common.output_directories import OutputFolderForTests
from InnerEye.ML import model_testing, model_training
from InnerEye.ML.common import ModelExecutionMode
from InnerEye.ML.metrics import InferenceMetricsForClassification
from Tests.ML.configs.ClassificationModelForTesting2D import ClassificationModelForTesting2D
from Tests.ML.util import get_default_checkpoint_handler


@pytest.mark.parametrize("use_mixed_precision", [False])
def test_train_2d_classification_model(test_output_dirs: OutputFolderForTests,
                                       use_mixed_precision: bool) -> None:
    """
    Test training and testing of 2d classification models.
    """
    logging_to_stdout(logging.DEBUG)
    config = ClassificationModelForTesting2D()
    config.set_output_to(test_output_dirs.root_dir)

    # Train for 4 epochs, checkpoints at epochs 2 and 4
    config.num_epochs = 4
    config.use_mixed_precision = use_mixed_precision

    checkpoint_handler = get_default_checkpoint_handler(model_config=config,
                                                        project_root=Path(test_output_dirs.root_dir))
    model_training_result = model_training.model_train(config, checkpoint_handler=checkpoint_handler)
    assert model_training_result is not None
    expected_learning_rates = [0.0001, 9.99971e-05, 9.99930e-05, 9.99861e-05]

    expected_train_loss = [0.705931, 0.698664, 0.694489, 0.693151]
    expected_val_loss = [1.078517, 1.140510, 1.199026, 1.248595]

    def extract_loss(results: List[MetricsDict]) -> List[float]:
        return [d.values()[MetricType.LOSS.value][0] for d in results]

    actual_train_loss = model_training_result.get_metric(is_training=True, metric_type=MetricType.LOSS)
    actual_val_loss = model_training_result.get_metric(is_training=False, metric_type=MetricType.LOSS)
    actual_learning_rates = model_training_result.get_metric(is_training=True, metric_type=MetricType.LEARNING_RATE)

    assert actual_train_loss == pytest.approx(expected_train_loss, abs=1e-6)
    assert actual_val_loss == pytest.approx(expected_val_loss, abs=1e-6)
    assert actual_learning_rates == pytest.approx(expected_learning_rates, rel=1e-5)
    test_results = model_testing.model_test(config, ModelExecutionMode.TRAIN, checkpoint_handler=checkpoint_handler)
    assert isinstance(test_results, InferenceMetricsForClassification)
