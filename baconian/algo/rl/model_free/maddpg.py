# from baconian.core.core import EnvSpec
# from baconian.algo.rl.rl_algo import ModelFreeAlgo, OffPolicyAlgo
# from baconian.config.dict_config import DictConfig
# from baconian.algo.rl.value_func.mlp_q_value import MLPQValueFunction
# from baconian.algo.rl.misc.replay_buffer import UniformRandomReplayBuffer, BaseReplayBuffer
# import tensorflow as tf
# import tensorflow.contrib as tf_contrib
# from baconian.common.sampler.sample_data import TransitionData
# from baconian.tf.tf_parameters import ParametersWithTensorflowVariable
# from baconian.config.global_config import GlobalConfig
# from baconian.common.special import *
# from baconian.algo.rl.policy.deterministic_mlp import DeterministicMLPPolicy
# from baconian.tf.util import *
# from baconian.common.misc import *
# from baconian.common.logging import record_return_decorator
# from baconian.core.status import register_counter_info_to_status_decorator
# from baconian.algo.placeholder_input import MultiPlaceholderInput
# from baconian.common.spaces.tuple import Tuple
# from copy import deepcopy
#
#
# class MADDPG(ModelFreeAlgo, OffPolicyAlgo, MultiPlaceholderInput):
#     required_key_dict = DictConfig.load_json(file_path=GlobalConfig().DEFAULT_MADDPG_REQUIRED_KEY_LIST)
#
#     @typechecked()
#     def __init__(self,
#                  single_agent_env_spec: EnvSpec,
#                  config_or_config_dict: (DictConfig, dict),
#                  value_func: MLPQValueFunction,
#                  policy: DeterministicMLPPolicy,
#                  schedule_param_list=None,
#                  name='maddpg',
#                  replay_buffer=None):
#         config = construct_dict_config(config_or_config_dict, self)
#         ensemble_env_spec = EnvSpec(
#             action_space=Tuple([deepcopy(single_agent_env_spec.action_space for _ in range(config('agent_counts')))]),
#             obs_space=Tuple([deepcopy(single_agent_env_spec.obs_space) for _ in range(config('agent_counts'))]))
#
#         ModelFreeAlgo.__init__(self, env_spec=ensemble_env_spec, name=name)
#
#         self.config = config
#         self.actor_list = [policy]
#         self.critic_list = [value_func]
#         self.target_actor_list = []
#         self.target_critic_list = []
#
#         for i in range(1, self.config('agent_counts')):
#             self.actor_list.append(self.actor_list[0].make_copy(name_scope='{}_{}'.format(self.name, i),
#                                                                 name='{}_{}'.format(self.name, i),
#                                                                 reuse=False))
#             self.critic_list.append(self.critic_list[0].make_copy(name_scope='{}_{}'.format(self.name, i),
#                                                                   name='{}_{}'.format(self.name, i),
#                                                                   reuse=False))
#         for i in range(self.config('agent_counts')):
#             self.target_actor_list.append(self.actor_list[i].make_copy(name_scope='target_{}_{}'.format(self.name, i),
#                                                                        name='target_{}_{}'.format(self.name, i),
#                                                                        reuse=False))
#             self.target_critic_list.append(self.critic_list[i].make_copy(name_scope='target_{}_{}'.format(self.name, i),
#                                                                          name='target_{}_{}'.format(self.name, i),
#                                                                          reuse=False))
#
#         if replay_buffer:
#             assert issubclass(replay_buffer, BaseReplayBuffer)
#             self.replay_buffer = replay_buffer
#         else:
#             self.replay_buffer = UniformRandomReplayBuffer(limit=self.config('REPLAY_BUFFER_SIZE'),
#                                                            action_shape=self.env_spec.action_shape,
#                                                            observation_shape=self.env_spec.obs_shape)
#
#         self.parameters = ParametersWithTensorflowVariable(tf_var_list=[],
#                                                            rest_parameters=dict(),
#                                                            to_scheduler_param_tuple=schedule_param_list,
#                                                            name='maddpg_param',
#                                                            source_config=config,
#                                                            require_snapshot=False)
#         with tf.variable_scope(name):
#             self.state_input = tf.placeholder(shape=[None, self.env_spec.flat_obs_dim], dtype=tf.float32)
#             self.reward_input = tf.placeholder(shape=[None, 1], dtype=tf.float32)
#             self.next_state_input = tf.placeholder(shape=[None, self.env_spec.flat_obs_dim], dtype=tf.float32)
#             self.done_input = tf.placeholder(shape=[None, 1], dtype=tf.bool)
#             self.target_q_input = tf.placeholder(shape=[None, 1], dtype=tf.float32)
#             done = tf.cast(self.done_input, dtype=tf.float32)
#             self.predict_q_value = (1. - done) * self.config('GAMMA') * self.target_q_input + self.reward_input
#             with tf.variable_scope('train'):
#                 self.critic_loss, self.critic_update_op, self.target_critic_update_op, self.critic_optimizer, self.critic_grads = self._setup_critic_loss()
#                 self.actor_loss, self.actor_update_op, self.target_actor_update_op, self.action_optimizer, self.actor_grads = self._set_up_actor_loss()
#
#         var_list = get_tf_collection_var_list(
#             '{}/train'.format(name)) + self.critic_optimizer.variables() + self.action_optimizer.variables()
#         self.parameters.set_tf_var_list(tf_var_list=sorted(list(set(var_list)), key=lambda x: x.name))
#         MultiPlaceholderInput.__init__(self,
#                                        sub_placeholder_input_list=[dict(obj=self.target_actor,
#                                                                         attr_name='target_actor',
#                                                                         ),
#                                                                    dict(obj=self.actor,
#                                                                         attr_name='actor'),
#                                                                    dict(obj=self.critic,
#                                                                         attr_name='critic'),
#                                                                    dict(obj=self.target_critic,
#                                                                         attr_name='target_critic')
#                                                                    ],
#                                        inputs=(self.state_input, self.reward_input, self.next_state_input,
#                                                self.done_input, self.target_q_input),
#                                        parameters=self.parameters)
#
#     @register_counter_info_to_status_decorator(increment=1, info_key='init', under_status='JUST_INITED')
#     def init(self, sess=None, source_obj=None):
#         for target_actor, actor in zip(self.target_actor_list, self.actor_list):
#             actor.init()
#             target_actor.init()
#         for target_critic, critic in zip(self.target_critic_list, self.critic_list):
#             critic.init()
#             target_critic.init(critic)
#
#         self.parameters.init()
#         if source_obj:
#             self.copy_from(source_obj)
#         super().init()
#
#     @record_return_decorator(which_recorder='self')
#     @register_counter_info_to_status_decorator(increment=1, info_key='train', under_status='TRAIN')
#     @typechecked
#     def train(self, batch_data=None, train_iter=None, sess=None, update_target=True) -> dict:
#         super(MADDPG, self).train()
#         tf_sess = sess if sess else tf.get_default_session()
#
#         batch_data = self.replay_buffer.sample(
#             batch_size=self.parameters('BATCH_SIZE')) if batch_data is None else batch_data
#         assert isinstance(batch_data, TransitionData)
#         train_iter_critic = self.parameters("CRITIC_TRAIN_ITERATION") if not train_iter else train_iter
#
#         critic_res = self._critic_train(batch_data, train_iter_critic, tf_sess, update_target)
#
#         train_iter_actor = self.parameters("ACTOR_TRAIN_ITERATION") if not train_iter else train_iter
#
#         actor_res = self._actor_train(batch_data, train_iter_actor, tf_sess, update_target)
#
#         return {**critic_res, **actor_res}
#
#     def _critic_train(self, batch_data, train_iter, sess, update_target) -> dict:
#         target_q = sess.run(
#             self._target_critic_with_target_actor_output.q_tensor,
#             feed_dict={
#                 self._target_critic_with_target_actor_output.state_input: batch_data.new_state_set,
#                 self.target_actor.state_input: batch_data.new_state_set
#             }
#         )
#         average_grads = None
#         average_loss = 0.0
#         for _ in range(train_iter):
#             loss, _, grads = sess.run(
#                 [self.critic_loss, self.critic_update_op, self.critic_grads
#                  ],
#                 feed_dict={
#                     self.target_q_input: target_q,
#                     self.critic.state_input: batch_data.state_set,
#                     self.critic.action_input: batch_data.action_set,
#                     self.done_input: batch_data.done_set,
#                     self.reward_input: batch_data.reward_set,
#                     **self.parameters.return_tf_parameter_feed_dict()
#                 }
#             )
#             if average_grads is None:
#                 average_grads = np.array(grads)
#             else:
#                 average_grads += np.array(grads)
#             average_loss += loss
#
#         if update_target is True:
#             sess.run(self.target_critic_update_op)
#         return dict(critic_average_loss=average_loss / train_iter)
#         # critic_avarge_grads=average_grads / train_iter)
#
#     def _actor_train(self, batch_data, train_iter, sess, update_target) -> dict:
#         average_loss = 0.0
#         average_grads = None
#         for _ in range(train_iter):
#             target_q, loss, _, grads = sess.run(
#                 [self._critic_with_actor_output.q_tensor, self.actor_loss, self.actor_update_op, self.actor_grads],
#                 feed_dict={
#                     self.actor.state_input: batch_data.state_set,
#                     self._critic_with_actor_output.state_input: batch_data.state_set,
#                     **self.parameters.return_tf_parameter_feed_dict()
#                 }
#             )
#             if average_grads is None:
#                 average_grads = np.array(grads)
#             else:
#                 average_grads += np.array(grads)
#             average_loss += loss
#         if update_target is True:
#             sess.run(self.target_actor_update_op)
#         return dict(actor_average_loss=average_loss / train_iter)
#         # actor_average_grad=average_grads / train_iter)
#
#     @register_counter_info_to_status_decorator(increment=1, info_key='test', under_status='TEST')
#     def test(self, *arg, **kwargs) -> dict:
#         return super().test(*arg, **kwargs)
#
#     @typechecked
#     def predict(self, obs: np.ndarray, sess=None, batch_flag: bool = False):
#         tf_sess = sess if sess else tf.get_default_session()
#         feed_dict = {
#             self.state_input: make_batch(obs, original_shape=self.env_spec.obs_shape),
#             **self.parameters.return_tf_parameter_feed_dict()
#         }
#         return self.actor.forward(obs=obs, sess=tf_sess, feed_dict=feed_dict)
#
#     @typechecked
#     def append_to_memory(self, samples: TransitionData):
#         iter_samples = samples.return_generator()
#
#         for obs0, obs1, action, reward, terminal1 in iter_samples:
#             self.replay_buffer.append(obs0=obs0,
#                                       obs1=obs1,
#                                       action=action,
#                                       reward=reward,
#                                       terminal1=terminal1)
#
#     @record_return_decorator(which_recorder='self')
#     def save(self, global_step, save_path=None, name=None, **kwargs):
#         save_path = save_path if save_path else GlobalConfig().DEFAULT_MODEL_CHECKPOINT_PATH
#         name = name if name else self.name
#         MultiPlaceholderInput.save(self, save_path=save_path, global_step=global_step, name=name, **kwargs)
#         return dict(check_point_save_path=save_path, check_point_save_global_step=global_step,
#                     check_point_save_name=name)
#
#     @record_return_decorator(which_recorder='self')
#     def load(self, path_to_model, model_name, global_step=None, **kwargs):
#         MultiPlaceholderInput.load(self, path_to_model, model_name, global_step, **kwargs)
#         return dict(check_point_load_path=path_to_model, check_point_load_global_step=global_step,
#                     check_point_load_name=model_name)
#
#     def _setup_critic_loss(self):
#         reg_loss = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES, scope=self.critic.name_scope)
#         loss = tf.reduce_sum((self.predict_q_value - self.critic.q_tensor) ** 2) + tf.reduce_sum(reg_loss)
#         optimizer = tf.train.AdamOptimizer(learning_rate=self.parameters('CRITIC_LEARNING_RATE'))
#         grads = tf.gradients(loss, self.critic.parameters('tf_var_list'))
#         if self.parameters('critic_clip_norm') is not None:
#             grads = [tf.clip_by_norm(grad, clip_norm=self.parameters('critic_clip_norm')) for grad in grads]
#         grads_var_pair = zip(grads, self.critic.parameters('tf_var_list'))
#         optimize_op = optimizer.apply_gradients(grads_var_pair)
#         op = []
#         for var, target_var in zip(self.critic.parameters('tf_var_list'),
#                                    self.target_critic.parameters('tf_var_list')):
#             ref_val = self.parameters('DECAY') * target_var + (1.0 - self.parameters('DECAY')) * var
#             op.append(tf.assign(target_var, ref_val))
#
#         return loss, optimize_op, op, optimizer, grads
#
#     def _set_up_actor_loss(self):
#         reg_loss = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES, scope=self.actor.name_scope)
#
#         loss = -tf.reduce_mean(self._critic_with_actor_output.q_tensor) + tf.reduce_sum(reg_loss)
#         grads = tf.gradients(loss, self.actor.parameters('tf_var_list'))
#         if self.parameters('actor_clip_norm') is not None:
#             grads = [tf.clip_by_norm(grad, clip_norm=self.parameters('actor_clip_norm')) for grad in grads]
#         grads_var_pair = zip(grads, self.actor.parameters('tf_var_list'))
#         optimizer = tf.train.AdamOptimizer(learning_rate=self.parameters('ACTOR_LEARNING_RATE'))
#         optimize_op = optimizer.apply_gradients(grads_var_pair)
#         op = []
#         for var, target_var in zip(self.actor.parameters('tf_var_list'),
#                                    self.target_actor.parameters('tf_var_list')):
#             ref_val = self.parameters('DECAY') * target_var + (1.0 - self.parameters('DECAY')) * var
#             op.append(tf.assign(target_var, ref_val))
#
#         return loss, optimize_op, op, optimizer, grads
