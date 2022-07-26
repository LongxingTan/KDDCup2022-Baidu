#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Longxing Tan, tanlongxing888@163.com

import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Dropout, GRU


class TokenEmbedding(tf.keras.layers.Layer):
    """ 
    x: batch * time * feature
    outout: batch * time * new_attention_size）
    """
    def __init__(self, embed_size):
        super(TokenEmbedding, self).__init__()
        self.embed_size = embed_size

    def build(self, input_shape):
        self.token_weights = self.add_weight(
            name='token_weights',
            shape=[input_shape[-1], self.embed_size],
            initializer=tf.random_normal_initializer(mean=0., stddev=self.embed_size ** -0.5))
        super(TokenEmbedding, self).build(input_shape)

    def call(self, x):
        y = tf.einsum('bsf,fk->bsk', x, self.token_weights)
        return y

    def get_config(self):
        config = {
            'embed_size': self.embed_size
        }
        base_config = super(TokenEmbedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class TokenRnnEmbedding(tf.keras.layers.Layer):
    def __init__(self, embed_size) -> None:
        super().__init__()
        self.embed_size = embed_size
    
    def build(self, input_shape):
        self.rnn = GRU(self.embed_size, return_sequences=True, return_state=True)
        super().build(input_shape)
    
    def call(self, x):
        y, _ = self.rnn(x)
        return y
    
    def get_config(self):
        config = {
            'embed_size': self.embed_size
        }
        base_config = super(TokenRnnEmbedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class PositionalEmbedding(tf.keras.layers.Layer):
    def __init__(self, max_len=5000):
        super(PositionalEmbedding, self).__init__()
        self.max_len = max_len

    def build(self, input_shape):
        super(PositionalEmbedding, self).build(input_shape)

    def call(self, x, masking=True):
        E = x.get_shape().as_list()[-1]  # static
        batch_size, seq_length = tf.shape(x)[0], tf.shape(x)[1]  # dynamic

        position_ind = tf.tile(tf.expand_dims(tf.range(seq_length), 0), [batch_size, 1])  # => batch_size * seq_length
        position_enc = np.array(
            [[pos / np.power(10000, (i - i % 2) / E) for i in range(E)] for pos in range(self.max_len)])

        position_enc[:, 0::2] = np.sin(position_enc[:, 0::2])
        position_enc[:, 1::2] = np.cos(position_enc[:, 1::2])
        position_enc = tf.convert_to_tensor(position_enc, tf.float32)  # (maxlen, E)

        outputs = tf.nn.embedding_lookup(position_enc, position_ind)
        if masking:
            outputs = tf.where(tf.equal(x, 0), x, outputs)
        return tf.cast(outputs, tf.float32)

    def get_config(self):
        config = {
            'max_len': self.max_len
        }
        base_config = super(PositionalEmbedding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))


class PositionalEncoding(tf.keras.layers.Layer):
    def __init__(self, max_len):
        super(PositionalEncoding, self).__init__()
        self.max_len = max_len

    def build(self, input_shape):
        super(PositionalEncoding, self).build(input_shape)

    def call(self, x, masking=True):
        E = x.get_shape().as_list()[-1]  # static
        batch_size, seq_length = tf.shape(x)[0], tf.shape(x)[1]  # dynamic
        with tf.name_scope('position_encode'):
            position_ind = tf.tile(tf.expand_dims(tf.range(seq_length), 0), [batch_size, 1])  # => batch_size * seq_length
            position_enc = np.array(
                [[pos / np.power(10000, (i - i % 2) / E) for i in range(E)] for pos in range(self.max_len)])

            position_enc[:, 0::2] = np.sin(position_enc[:, 0::2])
            position_enc[:, 1::2] = np.cos(position_enc[:, 1::2])
            position_enc = tf.convert_to_tensor(position_enc, tf.float32)  # (maxlen, E)

            outputs = tf.nn.embedding_lookup(position_enc, position_ind)
            if masking:
                outputs = tf.where(tf.equal(x, 0), x, outputs)
        return tf.cast(outputs, tf.float32)

    def get_config(self):
        config = {
            'max_len': self.max_len
        }
        base_config = super(PositionalEncoding, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

        

class DataEmbedding(tf.keras.layers.Layer):
    def __init__(self, embed_size, dropout=0.1):
        super(DataEmbedding, self).__init__()
        self.value_embedding = TokenEmbedding(embed_size)
        self.positional_embedding = PositionalEncoding(embed_size)
        self.dropout = Dropout(dropout)

    def build(self, input_shape):
        super(DataEmbedding, self).build(input_shape)

    def call(self, x):
        ve = self.value_embedding(x)
        pe = self.positional_embedding(ve)
        return self.dropout(ve + pe)

    def get_config(self):
        base_config = super(DataEmbedding, self).get_config()
        return base_config
