from baconian.envs.gym_env import GymEnv
from baconian.test.tests.set_up.setup import TestWithLogSet
from gym import make


class TestEnv(TestWithLogSet):
    def test_gym_env(self):
        a = GymEnv('Acrobot-v1')
        a.set_status('TRAIN')
        self.assertEqual(a.total_step_count_fn(), 0)
        self.assertEqual(a._last_reset_point, 0)
        a.init()
        a.seed(10)
        a.reset()
        self.assertEqual(a.total_step_count_fn(), 0)
        self.assertEqual(a._last_reset_point, 0)
        for i in range(1000):
            new_st, re, done, _ = a.step(action=a.action_space.sample())
            self.assertEqual(a.total_step_count_fn(), i + 1)
            if done is True:
                a.reset()
                self.assertEqual(a._last_reset_point, a.total_step_count_fn())
                self.assertEqual(a._last_reset_point, i + 1)

    def test_all_get_state(self):
        type_list = []
        for id in GymEnv._all_gym_env_id:
            try:
                env = make(id)
                type_list.append(type(env).__name__)
                env.reset()
                st = env.get_state()
                self.assertTrue(env.observation_space.contains(st))
                assert env.observation_space.contains(st)
            except BaseException:
                print("{} is not found".format(id))
        print(set(type_list))
