import shutil
import os
import subprocess
import logging
from collections import namedtuple

from pelican import signals
from pelican.generators import Generator


logger = logging.getLogger(__name__)
Issue = namedtuple('Issue', (
    'source',
    'save_as',
    'title',
    'frontpage',
))


class IssueGenerator(Generator):
    def __init__(self, *args, **kwargs):
        super(IssueGenerator, self).__init__(*args, **kwargs)
        signals.static_generator_init.send(self)

    def generate_context(self):
        self.issues = []
        for filename in self.get_files(self.settings['ISSUE_PATHS'],
                                       extensions='pdf'):
            issue_number = self.issue_number_from_filename(filename)
            title = self.settings['ISSUE_TITLE'].format(issue_number=issue_number)
            issue = Issue(
                source=os.path.join(self.path, filename),
                save_as=filename,
                title=title,
                frontpage=self.pdf_filename_to_jpg(filename),
            )
            self.issues.append(issue)
        self._update_context(('issues',))

        self.context['ISSUES'] = self.issues
        signals.static_generator_finalized.send(self)

    def generate_output(self, writer):
        for issue in self.context['issues']:
            source_path = os.path.join(self.path, issue.source)
            save_as = os.path.join(self.output_path, issue.save_as)

            try:
                os.makedirs(os.path.dirname(save_as))
            except OSError:
                # Path already exists, no worries
                pass

            shutil.copy2(source_path, save_as)
            logger.info('Copying %s to %s', issue.source, issue.save_as)

            self.extract_frontpage(
                issue.source,
                os.path.join(self.output_path, issue.frontpage)
            )

    def extract_frontpage(self, source, save_as):
        subprocess.call([
            'convert',
            '{input}[0]'.format(input=source),
            '{output}'.format(output=save_as),
            ])

    def pdf_filename_to_jpg(self, filename):
        return '%s.jpg' % filename.rsplit('.', 1)[0]

    def issue_number_from_filename(self, filename):
        return int(os.path.basename(filename).rsplit('.', 1)[0])


def get_generators(generators):
    return IssueGenerator


def register():
    signals.get_generators.connect(get_generators)
