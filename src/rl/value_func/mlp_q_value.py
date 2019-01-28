from src.rl.value_func.value_func import ValueFunction
import typeguard as tg
from src.envs.env_spec import EnvSpec
import overrides
import numpy as np
import tensorflow as tf
from typeguard import typechecked
from src.tf.tf_parameters import TensorflowParameters
from src.tf.mlp import MLP


class MLPQValueFunction(ValueFunction):
    """
    Multi Layer Q Value Function, based on Tensorflow, take the state and action as input,
    return the Q value for all action/ input action.
    """

    @tg.typechecked
    def __init__(self,
                 env_spec: EnvSpec,
                 name_scope: str,
                 input_norm: bool,
                 output_norm: bool,
                 output_low: (list, np.ndarray, None),
                 output_high: (list, np.ndarray, None),
                 mlp_config: list):
        self.name_scope = name_scope
        self.mlp_config = mlp_config
        self.input_norm = input_norm
        self.output_norm = output_norm
        self.output_low = output_low
        self.output_high = output_high

        with tf.variable_scope(self.name_scope):
            self.state_ph = tf.placeholder(shape=[None, env_spec.flat_obs_dim], dtype=tf.float32, name='state_ph')
            self.action_ph = tf.placeholder(shape=[None, env_spec.flat_action_dim], dtype=tf.float32, name='action_ph')
            self.mlp_input_ph = tf.concat([self.state_ph, self.action_ph], axis=1, name='state_action_input')

        self.mlp_net = MLP(input_ph=self.mlp_input_ph,
                           mlp_config=mlp_config,
                           input_norm=input_norm,
                           output_norm=output_norm,
                           output_high=output_high,
                           output_low=output_low,
                           name_scope=name_scope,
                           net_name='mlp')
        self.q_tensor = self.mlp_net.output
        parameters = TensorflowParameters(tf_var_list=self.mlp_net.var_list,
                                          rest_parameters=dict(),
                                          name='mlp_q_value_function_tf_param',
                                          auto_init=False)

        super(MLPQValueFunction, self).__init__(env_spec=env_spec, parameters=parameters)

    @overrides.overrides
    def copy(self, obj: ValueFunction) -> bool:
        assert super().copy(obj) is True
        self.parameters.copy_from(source_parameter=obj.parameters)
        return True

    @typechecked
    @overrides.overrides
    def forward(self, obs: (np.ndarray, list), action: (np.ndarray, list), sess=tf.get_default_session(), *args,
                **kwargs):
        feed_dict = {
            self.state_ph: obs,
            self.action_ph: action,
            **self.parameters.return_tf_parameter_feed_dict()
        }
        q = sess.run(self.q_tensor,
                     feed_dict=feed_dict)
        return q

    def init(self, source_obj=None):
        self.parameters.init()
        if source_obj:
            self.copy(obj=source_obj)

    def make_copy(self, *args, **kwargs):
        copy_mlp_q_value = MLPQValueFunction(env_spec=self.env_spec,
                                             name_scope=kwargs['name_scope'],
                                             input_norm=self.input_norm,
                                             output_norm=self.output_norm,
                                             output_low=self.output_low,
                                             output_high=self.output_high,
                                             mlp_config=self.mlp_config)
        return copy_mlp_q_value