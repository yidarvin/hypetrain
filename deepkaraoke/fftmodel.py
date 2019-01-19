import torch
import torch.nn as nn
import numpy as np
import submodules
from network import Network
import utils
from GLOBALS import FLAGS, GLOBAL


class Generator(Network):

    def BuildModel(self):
        n_fft, fft_channels, _ = utils.NFFT()
        # TODO: Use mel.
        # input_channels = FLAGS.n_mels + fft_channels
        input_channels = 2 * fft_channels
        layer_defs = []
        layer_defs.append(nn.Conv1d(input_channels, 256, 1, 1))
        for i in range(50):
            layer_defs.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
        layer_defs.append(nn.Conv1d(256, input_channels, 1, 1))
        return nn.Sequential(*layer_defs)

    def preprocess(self, data):
        ret = {
            'vocal_stft': [],
            'vocal_mel': [],
            'offvocal_stft': [],
            'offvocal_mel': [],
        }
        for d in data:
            data_vocal = d.data[0]
            stft_vocal = utils.STFT(data_vocal)
            data_offvocal = d.data[1]
            stft_offvocal = utils.STFT(data_offvocal)
            ret['vocal_stft'].append(stft_vocal)
            ret['vocal_mel'].append(utils.MelSpectrogram(stft_vocal))
            ret['offvocal_stft'].append(stft_offvocal)
            ret['offvocal_mel'].append(utils.MelSpectrogram(stft_offvocal))
        for k, v in ret.items():
          ret[k] = np.stack(v)
        return ret

    def forward(self, data):
        vocal_stacked = np.concatenate(
            (np.real(data['vocal_stft']), np.imag(data['vocal_stft'])), axis=1)
        vocal_stacked = torch.Tensor(vocal_stacked).cuda()
        return self.model.forward(vocal_stacked)

    def loss(self, prediction, data):
        n_fft, fft_channels, _ = utils.NFFT()
        predicted_real = prediction[:, :-fft_channels]
        predicted_imag = prediction[:, -fft_channels:]
        gt_real = torch.Tensor(np.real(data['offvocal_stft'])).cuda()
        gt_imag = torch.Tensor(np.imag(data['offvocal_stft'])).cuda()
        loss = torch.mean((predicted_real - gt_real)**2 +
                          (predicted_imag - gt_imag)**2)
        return loss

    def predict(self, data, summary_prefix=''):
        prediction = self.forward(data)
        prediction = prediction.detach().cpu().numpy()
        assert prediction.shape[0] == 1

        n_fft, fft_channels, _ = utils.NFFT()
        predicted_real = prediction[0, :-fft_channels]
        predicted_imag = prediction[0, -fft_channels:]
        predicted_mel = np.sqrt(predicted_real**2 + predicted_imag**2)
        if FLAGS.image_summaries:
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_onvocal',
                utils.PlotSpectrogram('gt onvocal', np.abs(data['vocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_offvocal',
                utils.PlotSpectrogram('gt offvocal',
                                      np.abs(data['offvocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/predicted_mel',
                utils.PlotSpectrogram('predicted', predicted_mel),
                GLOBAL.current_step)

        #predicted_magnitude = predicted_mel
        # predicted_magnitude = utils.InverseMelSpectrogram(predicted_mel)
        #predicted_stft = predicted_magnitude * np.exp(1j * np.angle(data['offvocal_stft'][0]))
        predicted_stft = predicted_real + 1j * predicted_imag
        result = utils.InverseSTFT(predicted_stft)
        return result

class ResNetAux(nn.Module):
    
    def __init__(self):
        super(ResNetAux, self).__init__()
        n_fft, fft_channels, _ = utils.NFFT()
        # TODO: Use mel.
        # input_channels = FLAGS.n_mels + fft_channels
        input_channels = 2 * fft_channels
        layer_defs_0 = []
        
        self.first_layer = nn.Conv1d(input_channels, 256, 1, 1)
        for i in range(10):
            layer_defs_0.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
        
        layer_defs_1 = []
        for i in range(10):
            layer_defs_1.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
            
        layer_defs_2 = []
        for i in range(10):
            layer_defs_2.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
            
        layer_defs_3 = []
        for i in range(10):
            layer_defs_3.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
            
        layer_defs_4 = []
        for i in range(10):
            layer_defs_4.append(submodules.ResNetModule1d(256, 256, 3, 1, 1, 1))
            
        self.branch_0 = nn.Sequential(*layer_defs_0)
        self.branch_1 = nn.Sequential(*layer_defs_1)
        self.branch_2 = nn.Sequential(*layer_defs_2)
        self.branch_3 = nn.Sequential(*layer_defs_3)
        self.branch_4 = nn.Sequential(*layer_defs_4)
        self.aux_0 = nn.Conv1d(256, input_channels, 1, 1)
        self.aux_1 = nn.Conv1d(256, input_channels, 1, 1)
        self.aux_2 = nn.Conv1d(256, input_channels, 1, 1)
        self.aux_3 = nn.Conv1d(256, input_channels, 1, 1)
        self.aux_4 = nn.Conv1d(256, input_channels, 1, 1)
    
    def forward(self, x):
        out = self.first_layer(x)
        out = self.branch_0(out)
        
        outputs = []
        
        aux_0 = self.aux_0(out)
        outputs.append(aux_0)
        
        out = self.branch_1(out)
        aux_1 = self.aux_1(out)
        outputs.append(aux_1)
        
        out = self.branch_1(out)
        aux_2 = self.aux_1(out)
        outputs.append(aux_2)
        
        out = self.branch_1(out)
        aux_3 = self.aux_1(out)
        outputs.append(aux_3)
        
        out = self.branch_1(out)
        aux_4 = self.aux_1(out)
        outputs.append(aux_4)
        
        return outputs
    
class ResNetAuxGeneral(nn.Module):
    
    def __init__(self, output_layer_list):
        super(ResNetAux, self).__init__()
        n_fft, fft_channels, _ = utils.NFFT()
        # TODO: Use mel.
        # input_channels = FLAGS.n_mels + fft_channels
        input_channels = 2 * fft_channels
        layer_defs_0 = []
        self.output_layer_list = output_layer_list
        
        self.first_layer = nn.Conv1d(input_channels, 256, 1, 1)
        self.first_relu = nn.ReLU()
        for i in range(50):
            exec('self.layer_%d = submodules.ResNetModule1d(256, 256, 3, 1, 1, 1)'%i)
        for i in range(len(self.output_layer_list)):    
            exec('self.aux_%d = nn.Conv1d(256, input_channels, 1, 1)'%i)
                 
    
    def forward(self, x):
        out = self.first_layer(x)
        out = self.first_relu(out)
        out = self.branch_0(out)
        
        current_layer = 0
        outputs = []
        
        for i in range(len(self.output_layer_list)):
            for j in range(current_layer, self.output_layer_list[i]):
                exec('out = self.layer_%d(out)'%j)
                exec('outputs.append(self.aux_%d(out))'%i)
        
        return outputs
        
    
class GeneratorDeepSupervision(Network):

    def BuildModel(self):
        return ResNetAux()

    def preprocess(self, data):
        ret = {
            'vocal_stft': [],
            'vocal_mel': [],
            'offvocal_stft': [],
            'offvocal_mel': [],
        }
        for d in data:
            data_vocal = d.data[0]
            stft_vocal = utils.STFT(data_vocal)
            data_offvocal = d.data[1]
            stft_offvocal = utils.STFT(data_offvocal)
            ret['vocal_stft'].append(stft_vocal)
            ret['vocal_mel'].append(utils.MelSpectrogram(stft_vocal))
            ret['offvocal_stft'].append(stft_offvocal)
            ret['offvocal_mel'].append(utils.MelSpectrogram(stft_offvocal))
        for k, v in ret.items():
          ret[k] = np.stack(v)
        return ret

    def forward(self, data):
        vocal_stacked = np.concatenate(
            (np.real(data['vocal_stft']), np.imag(data['vocal_stft'])), axis=1)
        vocal_stacked = torch.Tensor(vocal_stacked).cuda()
        return self.model.forward(vocal_stacked)

    def loss(self, prediction, data):
        n_fft, fft_channels, _ = utils.NFFT()
        predicted_real = prediction[:, :-fft_channels]
        predicted_imag = prediction[:, -fft_channels:]
        gt_real = torch.Tensor(np.real(data['offvocal_stft'])).cuda()
        gt_imag = torch.Tensor(np.imag(data['offvocal_stft'])).cuda()
        loss = torch.mean((predicted_real - gt_real)**2 +
                          (predicted_imag - gt_imag)**2)
        return loss

    def predict(self, data, summary_prefix='', aux_weights = None):
        prediction = self.forward(data)
        if FLAGS.model_name == 'GeneratorDeepSupervision':
            prediction = torch.sum(torch.cat([(aux_weights[i]*prediction[i]).unsqueeze(0) for i in range(len(prediction))],0),0)
        prediction = prediction.detach().cpu().numpy()
        assert prediction.shape[0] == 1

        n_fft, fft_channels, _ = utils.NFFT()
        predicted_real = prediction[0, :-fft_channels]
        predicted_imag = prediction[0, -fft_channels:]
        predicted_mel = np.sqrt(predicted_real**2 + predicted_imag**2)
        if FLAGS.image_summaries:
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_onvocal',
                utils.PlotSpectrogram('gt onvocal', np.abs(data['vocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_offvocal',
                utils.PlotSpectrogram('gt offvocal',
                                      np.abs(data['offvocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/predicted_mel',
                utils.PlotSpectrogram('predicted', predicted_mel),
                GLOBAL.current_step)

        #predicted_magnitude = predicted_mel
        # predicted_magnitude = utils.InverseMelSpectrogram(predicted_mel)
        #predicted_stft = predicted_magnitude * np.exp(1j * np.angle(data['offvocal_stft'][0]))
        predicted_stft = predicted_real + 1j * predicted_imag
        result = utils.InverseSTFT(predicted_stft)
        return result

class AutoregressiveGenerator(Generator):

    NUM_LAYERS = 50
    CONV_SIZE = 3

    def BuildModel(self):
        n_fft, fft_channels, _ = utils.NFFT()
        # Input is (magnitude + phase) for both (onvocal, prev_offvocal).
        # Output is (magnitude + phase) for offvocal.
        # TODO: Use mel.
        # input_channels = 2 * (FLAGS.n_mels + fft_channels)
        # output_channels = FLAGS.n_mels + fft_channels
        input_channels = 2 * (2 * fft_channels)
        output_channels = 2 * fft_channels
        layer_defs = []
        layer_defs.append(nn.Conv1d(input_channels, 256, 1, 1))
        for i in range(self.NUM_LAYERS):
            layer_defs.append(submodules.ResNetModule1d(
                256, 256, self.CONV_SIZE, 1, 1, 1, causal=True))
        layer_defs.append(nn.Conv1d(256, output_channels, 1, 1))
        return nn.Sequential(*layer_defs)

    def _ReceptiveField(self):
        return (self.CONV_SIZE - 1) * self.NUM_LAYERS

    def forward(self, data):
        vocal_stacked = np.concatenate(
            (np.real(data['vocal_stft']), np.imag(data['vocal_stft'])), axis=1)
        offvocal_stacked = np.concatenate(
            (np.real(data['offvocal_stft']), np.imag(data['offvocal_stft'])),
            axis=1)
        # Shift offvocal forward by 1 sample for next sample prediction.
        offvocal_stacked = np.concatenate(
            (np.zeros_like(offvocal_stacked[:, :, :1]),
             offvocal_stacked[:, :, :-1]), axis=2)
        input = np.concatenate((vocal_stacked, offvocal_stacked), axis=1)
        return self.model.forward(torch.Tensor(input).cuda())

    def loss(self, prediction, data):
        n_fft, fft_channels, _ = utils.NFFT()
        predicted_real = prediction[:, :-fft_channels]
        predicted_imag = prediction[:, -fft_channels:]
        gt_real = torch.Tensor(np.real(data['offvocal_stft'])).cuda()
        gt_imag = torch.Tensor(np.imag(data['offvocal_stft'])).cuda()
        loss = torch.mean((predicted_real - gt_real)**2 +
                          (predicted_imag - gt_imag)**2)

        if GLOBAL.current_step % 1000 == 0 and FLAGS.image_summaries:
            GLOBAL.summary_writer.add_image(
                'train/gt_mel_onvocal',
                utils.PlotSpectrogram('gt onvocal', np.abs(data['vocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                'train/gt_mel_offvocal',
                utils.PlotSpectrogram('gt offvocal',
                                      np.abs(data['offvocal_stft'][0])),
                GLOBAL.current_step)
            predicted_magnitude = np.abs(predicted_real[0].detach().cpu().numpy() +
                                         1j * predicted_imag[0].detach().cpu().numpy())
            GLOBAL.summary_writer.add_image(
                'train/predicted_mel',
                utils.PlotSpectrogram('predicted', predicted_magnitude),
                GLOBAL.current_step)
        return loss

    def predict(self, data, summary_prefix=''):
        _, fft_channels, _ = utils.NFFT()
        assert data['vocal_stft'].shape[0] == 1
        assert data['vocal_stft'].shape[1] == fft_channels
        seqlen = data['vocal_stft'].shape[2]
        prediction = np.zeros((1, 2 * fft_channels, seqlen))
        for i in range(seqlen):
            # Decoding window INCLUDES i because offvocal_stft is shifted by 1
            # in forward.
            decode_window_start = max(0, i - self._ReceptiveField())
            data_i = {}
            data_i['vocal_stft'] = (
                data['vocal_stft'][:, :, decode_window_start:i + 1])
            data_i['offvocal_stft'] = (
                prediction[:, :-fft_channels, decode_window_start:i + 1] +
                1j * prediction[:, -fft_channels:, decode_window_start:i + 1])
            prediction_i = self.forward(data_i)
            prediction[:, :, i] = prediction_i[:, :, -1].detach().cpu().numpy()

        predicted_real = prediction[0, :-fft_channels]
        predicted_imag = prediction[0, -fft_channels:]
        predicted_mel = np.sqrt(predicted_real**2 + predicted_imag**2)

        if FLAGS.image_summaries:
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_onvocal',
                utils.PlotSpectrogram('gt onvocal', np.abs(data['vocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/gt_mel_offvocal',
                utils.PlotSpectrogram('gt offvocal',
                                      np.abs(data['offvocal_stft'][0])),
                GLOBAL.current_step)
            GLOBAL.summary_writer.add_image(
                summary_prefix + '/predicted_mel',
                utils.PlotSpectrogram('predicted', predicted_mel),
                GLOBAL.current_step)

        predicted_magnitude = predicted_mel
        # predicted_magnitude = utils.InverseMelSpectrogram(predicted_mel)
        predicted_stft = predicted_magnitude * np.exp(1j * np.angle(data['offvocal_stft'][0]))
        # predicted_stft = predicted_real + 1j * predicted_imag
        result = utils.InverseSTFT(predicted_stft)
        return result


class Flatten(nn.Module):

    def forward(self, input):
        return input.view(input.size(0), -1)


class Discriminator(Network):

    def BuildModel(self):
        n_fft, fft_channels, _ = utils.NFFT()

        input_channels = 2 * fft_channels
        layer_defs = []
        layer_defs.append(submodules.convbn_1d(input_channels, 256, 3, 2, 1, 1))
        layer_defs.append(submodules.convbn_1d(256, 256, 3, 1, 1, 1))
        for i in range(4):
            layer_defs.append(submodules.convbn_1d(256, 256, 3, 1, 1, 1))
            layer_defs.append(submodules.convbn_1d(256, 256, 3, 1, 1, 1))
        layer_defs.append(Flatten())
        layer_defs.append(nn.Linear(15360,2))
        return nn.Sequential(*layer_defs)

    def loss(self, input, labels):
        criterion = nn.CrossEntropyLoss()
        return criterion(input, labels)

    def forward(self, data):
        
        if type(data) is dict:
            vocal_stacked = np.concatenate(
                (np.real(data['offvocal_stft']),
                 np.imag(data['offvocal_stft'])),
                axis=1)
            data = torch.Tensor(vocal_stacked).cuda()
        return self.model.forward(data)
