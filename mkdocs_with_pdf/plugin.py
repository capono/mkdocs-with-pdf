import logging
import os
from timeit import default_timer as timer

from mkdocs.plugins import BasePlugin

from .generator import Generator
from .options import Options

logging.getLogger(__name__)


class WithPdfPlugin(BasePlugin):

    config_scheme = Options.config_scheme

    def __init__(self):
        self._logger = logging.getLogger('mkdocs.with-pdf')
        self._logger.setLevel(logging.INFO)

        self.generator = None
        self.enabled = False

        self._num_pages = 0
        self._total_time = 0

    def on_config(self, config):

        if 'enabled_if_env' in self.config:
            env_name = self.config['enabled_if_env']
            if env_name:
                self.enabled = os.environ.get(env_name) == '1'
                if not self.enabled:
                    self._logger.warning(
                        'without generate PDF'
                        f'(set environment variable {env_name} to 1 to enable)'
                    )
                    return
            else:
                self.enabled = True
        else:
            self.enabled = True

        self._options = Options(self.config, config, self._logger)

        from weasyprint.logger import LOGGER
        if self._options.verbose:
            LOGGER.setLevel(logging.DEBUG)
            self._logger.setLevel(logging.DEBUG)
        else:
            LOGGER.setLevel(logging.ERROR)

        self.generator = Generator(options=self._options)

        '''
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        LOGGER.addHandler(handler)
        '''

    def on_nav(self, nav, config, files):
        if self.enabled:
            self.generator.on_nav(nav)
        return nav

    def on_post_page(self, output_content, page, config):
        if not self.enabled:
            return output_content

        self._num_pages += 1
        start = timer()
        pdf_path = self.get_path_to_pdf_from(page.file.dest_path)
        modified = self.generator.on_post_page(output_content, page, pdf_path)
        end = timer()
        self._total_time += (end - start)
        return modified

    def on_post_build(self, config):
        if not self.enabled:
            return

        start = timer()
        self.generator.on_post_build(config, self.config['output_path'])
        end = timer()
        self._total_time += (end - start)
        self._logger.info(
            f'Converting {self._num_pages} articles to PDF'
            f' took {self._total_time:.1f}s'
        )

    def get_path_to_pdf_from(self, start):
        pdf_split = os.path.split(self.config['output_path'])
        start_dir = os.path.split(start)[0]
        return os.path.join(
            os.path.relpath(
                pdf_split[0],
                start_dir),
            pdf_split[1])
