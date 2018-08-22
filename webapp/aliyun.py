
import json
from urllib import quote
from aliyunsdkcore.client import AcsClient
from aliyunsdkmts.request.v20140618 import SubmitJobsRequest
import oss2

class Aliyun(object):

    def __init__(self, logger):
        self.logger = logger

        access_key_id = ''.join('L_T_A_I_y_Y_j_Gr_5_G_f_O_H_J_F'.split('_'))
        access_key_secret = ''.join('F_D_W_g_H_Z_q_M_m_r_0_J_z_Y_Z_Q_x_b_E_s_d_E_L_a_K_l_7_5_T_5'.split('_'))
        mps_region_id = 'cn-hangzhou'

        self.oss_internal_location = 'oss-cn-hangzhou-internal'
        
        self.oss_location = 'oss-cn-hangzhou'
        self.oss_bucket = 'svea-flv'

        auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(auth, 'http://%s.aliyuncs.com' % (self.oss_location), self.oss_bucket)
        self.internal_bucket = oss2.Bucket(auth, 'http://%s.aliyuncs.com' % (self.oss_internal_location), self.oss_bucket)
        self.client = AcsClient(access_key_id, access_key_secret, mps_region_id);

    def upload_convert_get_link(self, _user, _filename, _bytes):
        src_video = 'flv'
        dest_video = 'mp4'

        src_path = "%s/%s/%s" % (src_video, _user, _filename)
        res = self.upload_bytes(src_path, _bytes)
        if not res: return None

        _filename = _filename[:-len(src_video)-1] + "." + dest_video
        dest_path = "%s/%s/%s" % (dest_video, _user, _filename)

        res = self.convert_file(src_path, dest_path)
        if not res: return None

        return dest_path

    def upload_local_file(self, src, dest):
        with open(src, 'rb') as fileobj:
            self.upload_bytes(dest, fileobj)

    def upload_bytes(self, dest, _bytes):
        try:
            self.internal_bucket.put_object(dest, _bytes)
            return True
        except Exception as e:
            self.logger.error(e)
            return False

    def get_aliyun_url(self, path):
        try:
            url = self.bucket.sign_url('GET', path, 60*60*24*7)
            self.logger.debug(url)
            return url
        except Exception as e:
            self.logger.error(e)

    def convert_file(self, oss_input_object, oss_output_object):

        pipeline_id = '8d377f7436914160b88f82f0de804473'
        template_id = 'f7abad32c12944b1944272c84dfd473a'
        
        request = SubmitJobsRequest.SubmitJobsRequest()
        request.set_accept_format('json')

        job_input = {'Location': self.oss_location,
                     'Bucket': self.oss_bucket,
                     'Object': quote(oss_input_object) }
        request.set_Input(json.dumps(job_input))

        output = {'OutputObject': quote(oss_output_object)}
        output['Container'] = {'Format': 'mp4'}
        output['Video'] = {'Codec': 'H.264',
                           'Bitrate': 1500,
                           'Width': 1280,
                           'Fps': 25}
        output['Audio'] = {'Codec': 'AAC',
                           'Bitrate': 128,
                           'Channels': 2,
                           'Samplerate': 44100}
        output['TemplateId'] = template_id
        outputs = [output]
        request.set_Outputs(json.dumps(outputs))
        request.set_OutputBucket(self.oss_bucket)
        request.set_OutputLocation(self.oss_location)

        request.set_PipelineId(pipeline_id)

        response_str = self.client.do_action_with_exception(request)
        response = json.loads(response_str)

        self.logger.debug('RequestId is:' + response['RequestId'])

        if response['JobResultList']['JobResult'][0]['Success']:
            self.logger.debug('JobId:' + response['JobResultList']['JobResult'][0]['Job']['JobId'])
            return True
        else:
            self.logger.error('SubmitJobs Failed code:' + response['JobResultList']['JobResult'][0]['Code'] + \
                   ' message:' + response['JobResultList']['JobResult'][0]['Message'])
            return False