"""Keep the ARM SDK pointcloud parameters scoped to the camera launch."""
import importlib.util
from pathlib import Path

import pytest
import yaml
from launch import LaunchContext
from launch.actions import OpaqueFunction
from launch.utilities import visit_all_entities_and_collect_futures

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('pointcloud', [False, True])
def test_accelerated_cloud_enable_and_color_are_scoped(monkeypatch, tmp_path, pointcloud):
    spec = importlib.util.spec_from_file_location('d435i_cloud_launch', ROOT / 'launch/bringup.launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = tmp_path / 'camera.yaml'
    config.write_text(yaml.safe_dump({'pointcloud': pointcloud}))
    monkeypatch.setattr(module, 'get_package_share_directory', lambda name: str(tmp_path))
    seen = []

    def observe(context):
        seen.append(dict(context.launch_configurations['global_params']))
        return []

    monkeypatch.setattr(module, 'IncludeLaunchDescription',
                        lambda *args, **kwargs: OpaqueFunction(function=observe))
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(config), unrelated='parent')
    original = dict(context.launch_configurations)
    for action in module._setup(context):
        visit_all_entities_and_collect_futures(action, context)
    assert seen == [{
        'pointcloud__neon_.enable': pointcloud,
        'pointcloud__neon_.stream_filter': 2,
        'pointcloud__neon_.stream_index_filter': 0,
    }]
    assert context.launch_configurations == original
