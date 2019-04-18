"""
DDPG bechmark on Pendulum
"""

from benchmark.dyna_benchmark.pendulum_conf import *
from baconian.common.noise import *
from baconian.common.schedules import *
from baconian.core.core import EnvSpec
from baconian.envs.gym_env import make
from baconian.algo.rl.value_func.mlp_q_value import MLPQValueFunction
from baconian.algo.rl.model_free.ddpg import DDPG
from baconian.algo.rl.policy.deterministic_mlp import DeterministicMLPPolicy
from baconian.core.agent import Agent
from baconian.core.experiment import Experiment
from baconian.config.global_config import GlobalConfig
from baconian.core.status import get_global_status_collect
from baconian.algo.dynamics.mlp_dynamics_model import ContinuousMLPGlobalDynamicsModel
from baconian.algo.rl.model_based.dyna import Dyna
from baconian.algo.dynamics.terminal_func.terminal_func import FixedEpisodeLengthTerminalFunc
from baconian.core.flow.dyna_flow import DynaFlow
from baconian.envs.gym_reward_func import REWARD_FUNC_DICT


def pendulum_task_fn():
    exp_config = PENDULUM_BENCHMARK_CONFIG_DICT
    GlobalConfig().set('DEFAULT_EXPERIMENT_END_POINT',
                       dict(TOTAL_AGENT_TRAIN_SAMPLE_COUNT=10000,
                            TOTAL_AGENT_TEST_SAMPLE_COUNT=None,
                            TOTAL_AGENT_UPDATE_COUNT=None))

    env = make('Pendulum-v0')
    name = 'benchmark'
    env_spec = EnvSpec(obs_space=env.observation_space,
                       action_space=env.action_space)

    mlp_q = MLPQValueFunction(env_spec=env_spec,
                              name_scope=name + '_mlp_q',
                              name=name + '_mlp_q',
                              **exp_config['MLPQValueFunction'])
    policy = DeterministicMLPPolicy(env_spec=env_spec,
                                    name_scope=name + '_mlp_policy',
                                    name=name + '_mlp_policy',
                                    output_low=env_spec.action_space.low,
                                    output_high=env_spec.action_space.high,
                                    **exp_config['DeterministicMLPPolicy'],
                                    reuse=False)

    ddpg = DDPG(
        env_spec=env_spec,
        policy=policy,
        value_func=mlp_q,
        name=name + '_ddpg',
        **exp_config['DDPG']
    )

    mlp_dyna = ContinuousMLPGlobalDynamicsModel(
        env_spec=env_spec,
        name_scope=name + '_mlp_dyna',
        name=name + '_mlp_dyna',
        output_low=env_spec.obs_space.low,
        output_high=env_spec.obs_space.high,
        **exp_config['DynamicsModel']
    )
    algo = Dyna(env_spec=env_spec,
                name=name + '_dyna_algo',
                model_free_algo=ddpg,
                dynamics_model=mlp_dyna,
                config_or_config_dict=dict(
                    dynamics_model_train_iter=10,
                    model_free_algo_train_iter=10
                ))
    algo.set_terminal_reward_function_for_dynamics_env(
        terminal_func=FixedEpisodeLengthTerminalFunc(max_step_length=env.unwrapped._max_episode_steps,
                                                     step_count_fn=algo.dynamics_env.total_step_count_fn),
        reward_func=REWARD_FUNC_DICT['Pendulum-v0']())
    agent = Agent(env=env, env_spec=env_spec,
                  algo=algo,
                  exploration_strategy=None,
                  noise_adder=AgentActionNoiseWrapper(noise=NormalActionNoise(),
                                                      noise_weight_scheduler=ConstantSchedule(value=0.3),
                                                      action_weight_scheduler=ConstantSchedule(value=1.0)),
                  name=name + '_agent')

    flow = DynaFlow(
        train_sample_count_func=lambda: get_global_status_collect()('TOTAL_AGENT_TRAIN_SAMPLE_COUNT'),
        config_or_config_dict=exp_config['DynaFlow'],
        func_dict={
            'train_algo': {'func': agent.train,
                           'args': list(),
                           'kwargs': dict(state='state_agent_training')},
            'train_algo_from_synthesized_data': {'func': agent.train,
                                                 'args': list(),
                                                 'kwargs': dict(state='state_agent_training')},
            'train_dynamics': {'func': agent.train,
                               'args': list(),
                               'kwargs': dict(state='state_dynamics_training')},
            'test_algo': {'func': agent.test,
                          'args': list(),
                          'kwargs': dict(sample_count=1, sample_trajectory_flag=True)},
            'test_dynamics': {'func': agent.algo.test_dynamics,
                              'args': list(),
                              'kwargs': dict(sample_count=10, env=env)},
            'sample_from_real_env': {'func': agent.sample,
                                     'args': list(),
                                     'kwargs': dict(sample_count=10,
                                                    env=agent.env,
                                                    in_which_status='TRAIN',
                                                    store_flag=True)},
            'sample_from_dynamics_env': {'func': agent.sample,
                                         'args': list(),
                                         'kwargs': dict(sample_count=1,
                                                        sample_type='trajectory',
                                                        env=agent.algo.dynamics_env,
                                                        in_which_status='TRAIN',
                                                        store_flag=False)}
        }
    )

    experiment = Experiment(
        tuner=None,
        env=env,
        agent=agent,
        flow=flow,
        name=name
    )
    experiment.run()
