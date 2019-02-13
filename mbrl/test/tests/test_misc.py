import unittest
from mbrl.envs.env_spec import EnvSpec
from gym.spaces import *
from mbrl.common.special import *
from mbrl.envs.gym_env import make
import numpy as np
from mbrl.test.tests.testSetup import BaseTestCase


class TestMisc(BaseTestCase):

    def create_env_spec(self):
        env = EnvSpec(obs_space=Box(low=0.0,
                                    high=1.0,
                                    shape=[2]),
                      action_space=Box(low=0.0,
                                       high=1.0,
                                       shape=[2]))
        return env

    def test_env_spec(self):
        env = self.create_env_spec()
        self.assertEqual(env.flat_obs_dim, 2)
        self.assertEqual(env.flat_action_dim, 2)

    def test_misc_func(self):
        env = make('Swimmer-v1')
        a = make_batch(v=np.array([env.action_space.sample() for _ in range(10)]),
                       original_shape=env.env_spec.action_shape)
        self.assertEqual(a.shape[0], 10)
        self.assertTrue(a.shape[1:] == env.env_spec.action_shape)
        for ac in a:
            self.assertTrue(env.action_space.contains(ac))

        a = make_batch(v=np.array([env.observation_space.sample() for _ in range(10)]),
                       original_shape=env.env_spec.obs_shape)
        self.assertTrue(a.shape[1:] == env.env_spec.obs_shape)
        for ac in a:
            self.assertTrue(env.observation_space.contains(ac))

        env = make('Acrobot-v1')
        a = make_batch(v=np.array([env.action_space.sample() for _ in range(10)]),
                       original_shape=env.env_spec.action_shape)
        self.assertEqual(a.shape[0], 10)

        self.assertTrue(a.shape[1:] == env.env_spec.action_shape)
        for ac in a:
            self.assertTrue(env.action_space.contains(ac))

        a = make_batch(v=np.array([env.observation_space.sample() for _ in range(10)]),
                       original_shape=env.env_spec.obs_shape)
        self.assertEqual(a.shape[0], 10)
        self.assertTrue(a.shape[1:] == env.env_spec.obs_shape)
        for ac in a:
            self.assertTrue(env.observation_space.contains(ac))