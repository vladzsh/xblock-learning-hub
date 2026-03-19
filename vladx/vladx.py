"""VladX Learning Hub -- an educational XBlock demonstrating the full XBlock API."""

import json
import logging
from datetime import datetime

from webob import Response
from web_fragments.fragment import Fragment
from importlib.resources import files

from xblock.core import XBlock
from xblock.fields import (
    String, Integer, Boolean, Float, List, Dict, DateTime, Any, Scope,
)

log = logging.getLogger(__name__)


@XBlock.needs('i18n')
@XBlock.wants('settings')
@XBlock.wants('user')
class VladXBlock(XBlock):
    """
    VladX Learning Hub -- an educational XBlock.

    Features: quiz with grading, thumbs voting, compact/full display mode,
    studio editing, children support, XML serialization, validation.
    """

    has_children = True
    has_score = True
    icon_class = 'problem'

    # --- Scope.content (BlockScope.DEFINITION + UserScope.NONE) ---

    question_text = String(
        display_name="Question text",
        help="The question displayed to students.",
        default="Which XBlock method is called to render the student view?",
        scope=Scope.content,
    )

    correct_answer = String(
        display_name="Correct answer",
        help="The correct answer to the question.",
        default="student_view",
        scope=Scope.content,
    )

    explanation = String(
        display_name="Explanation",
        help="Explanation shown after a correct answer.",
        default=(
            "The student_view() method is the primary XBlock view "
            "called by the LMS to display the block to students. "
            "It must return a Fragment containing HTML, CSS, and JavaScript."
        ),
        scope=Scope.content,
        xml_node=True,
    )

    # --- Scope.settings (BlockScope.USAGE + UserScope.NONE) ---

    display_name = String(
        display_name="Component name",
        help="Display name shown in the block header and course navigation.",
        default="VladX Learning Hub",
        scope=Scope.settings,
    )

    max_attempts = Integer(
        display_name="Max attempts",
        help="Maximum number of submission attempts allowed.",
        default=3,
        scope=Scope.settings,
    )

    weight = Float(
        display_name="Weight",
        help="Weight of this problem in the overall grade.",
        default=1.0,
        scope=Scope.settings,
    )

    due_date = DateTime(
        display_name="Due date",
        help="Deadline for submitting an answer (ISO format). None means no deadline.",
        default=None,
        scope=Scope.settings,
    )

    hints = List(
        display_name="Hints",
        help="List of text hints for the student.",
        default=["It's a Python method name", "It starts with 'student_'"],
        scope=Scope.settings,
    )

    options = Dict(
        display_name="Extra options",
        help="Dictionary of additional configuration parameters.",
        default={"show_explanation": True, "shuffle_hints": False},
        scope=Scope.settings,
    )

    allow_reset = Boolean(
        display_name="Allow reset",
        help="Whether students can reset their answer and start over.",
        default=True,
        scope=Scope.settings,
    )

    # --- Scope.user_state (BlockScope.USAGE + UserScope.ONE) ---

    student_answer = String(
        help="The answer entered by the student.",
        default="",
        scope=Scope.user_state,
    )

    attempts_used = Integer(
        help="Number of attempts used by the student.",
        default=0,
        scope=Scope.user_state,
    )

    is_submitted = Boolean(
        help="Whether the student has submitted at least once.",
        default=False,
        scope=Scope.user_state,
    )

    score_earned = Float(
        help="Score earned by the student.",
        default=0.0,
        scope=Scope.user_state,
    )

    student_data = Any(
        help="Arbitrary per-student data (Any field type demo).",
        default=None,
        scope=Scope.user_state,
    )

    voted = Boolean(
        help="Whether this student has voted on the question.",
        default=False,
        scope=Scope.user_state,
    )

    hint_index = Integer(
        help="Index of the last shown hint for this student.",
        default=0,
        scope=Scope.user_state,
    )

    # --- Scope.user_state_summary (BlockScope.USAGE + UserScope.ALL) ---

    total_submissions = Integer(
        help="Total number of submissions across all students.",
        default=0,
        scope=Scope.user_state_summary,
    )

    upvotes = Integer(
        help="Total upvotes from all students.",
        default=0,
        scope=Scope.user_state_summary,
    )

    downvotes = Integer(
        help="Total downvotes from all students.",
        default=0,
        scope=Scope.user_state_summary,
    )

    # --- Scope.preferences (BlockScope.TYPE + UserScope.ONE) ---

    display_mode = String(
        help="Preferred display mode: 'full' or 'compact'.",
        default="full",
        scope=Scope.preferences,
        values=["compact", "full"],
    )

    # --- Scope.user_info (BlockScope.ALL + UserScope.ONE) ---

    user_language = String(
        help="User's preferred language.",
        default="ru",
        scope=Scope.user_info,
    )

    # --- Helpers ---

    def resource_string(self, path):
        """Load a text resource from this package."""
        return files(__package__).joinpath(path).read_text(encoding="utf-8")

    # --- Views ---

    @XBlock.supports('multi_device')
    def student_view(self, context=None):
        """Render the primary student view."""
        html = self.resource_string("static/html/vladx.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/vladx.css"))
        frag.add_javascript(self.resource_string("static/js/src/vladx.js"))

        if self.children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                child_frag = self.runtime.render_child(child, 'student_view', context)
                # add_frag_resources копирует CSS и JS из дочернего Fragment
                # в родительский, чтобы стили и скрипты дочерних блоков работали.
                frag.add_fragment_resources(child_frag)
                # Добавляем HTML-содержимое дочернего блока в конец родительского.
                frag.add_content(child_frag.content)

        frag.initialize_js('VladXBlock')
        return frag

    def studio_view(self, context=None):
        """Render the Studio editing view."""
        html = self.resource_string("static/html/vladx_studio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/vladx.css"))
        frag.add_javascript(self.resource_string("static/js/src/vladx_studio.js"))
        frag.initialize_js('VladXStudio')
        return frag

    def author_view(self, context=None):
        """Render the Studio author preview (reuses student_view with a badge)."""
        frag = self.student_view(context)
        frag.add_content(
            '<div class="vladx-author-badge">Author mode (author_view)</div>'
        )
        return frag

    def fallback_view(self, view_name, context=None):
        """Handle undefined view names."""
        return Fragment(
            '<div class="vladx-fallback">'
            '<p><strong>VladX:</strong> View '
            '<code>{}</code> is not defined.</p>'
            '<p>Defined views: student_view, studio_view, author_view.</p>'
            '</div>'.format(view_name)
        )

    # --- Handlers ---

    @XBlock.json_handler
    def submit_answer(self, data, suffix=''):
        """Handle answer submission, check correctness, publish grade."""
        if self.attempts_used >= self.max_attempts:
            return {
                "success": False,
                "error": "All attempts used ({}/{})".format(
                    self.attempts_used, self.max_attempts
                ),
            }

        self.student_answer = data.get("answer", "")
        self.attempts_used += 1
        self.is_submitted = True
        self.total_submissions += 1

        is_correct = (
            self.student_answer.strip().lower()
            == self.correct_answer.strip().lower()
        )

        earned = self.weight if is_correct else 0.0
        self.score_earned = earned

        self.runtime.publish(self, 'grade', {
            'value': earned,
            'max_value': self.weight,
        })

        self.runtime.publish(self, 'xblock.vladx.answer_submitted', {
            'answer': self.student_answer,
            'is_correct': is_correct,
            'attempt': self.attempts_used,
        })

        self.student_data = {
            "last_answer": self.student_answer,
            "timestamp": str(datetime.utcnow()),
            "is_correct": is_correct,
        }

        return {
            "success": True,
            "is_correct": is_correct,
            "attempts_used": self.attempts_used,
            "max_attempts": self.max_attempts,
            "score": earned,
            "total_submissions": self.total_submissions,
            "explanation": self.explanation if is_correct else "",
        }

    @XBlock.json_handler
    def vote(self, data, suffix=''):
        """Handle thumbs up/down voting."""

        if self.voted:
            return {
                "success": True,
                "upvotes": self.upvotes,
                "downvotes": self.downvotes,
            }

        vote_type = data.get("vote_type")
        if vote_type not in ("up", "down"):
            return {"success": False, "error": "Invalid vote type: {}".format(vote_type)}

        if vote_type == "up":
            self.upvotes += 1
        else:
            self.downvotes += 1

        self.voted = True

        self.runtime.publish(self, 'xblock.vladx.voted', {
            'vote_type': vote_type,
        })

        return {
            "success": True,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
        }

    @XBlock.json_handler
    def save_settings(self, data, suffix=''):
        """Handle Studio settings save."""
        self.display_name = data.get("display_name", self.display_name)
        self.max_attempts = int(data.get("max_attempts", self.max_attempts))
        self.weight = float(data.get("weight", self.weight))
        self.allow_reset = bool(data.get("allow_reset", self.allow_reset))

        self.question_text = data.get("question_text", self.question_text)
        self.correct_answer = data.get("correct_answer", self.correct_answer)
        self.explanation = data.get("explanation", self.explanation)

        return {"success": True}

    @XBlock.json_handler
    def get_state(self, data, suffix=''):
        """Return current block state for JS initialization."""
        return {
            "student_answer": self.student_answer,
            "attempts_used": self.attempts_used,
            "is_submitted": self.is_submitted,
            "score_earned": self.score_earned,
            "voted": self.voted,
            "max_attempts": self.max_attempts,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "total_submissions": self.total_submissions,
            "display_mode": self.display_mode,
        }

    @XBlock.json_handler
    def toggle_display_mode(self, data, suffix=''):
        """Toggle display mode between 'compact' and 'full' (Scope.preferences)."""
        self.display_mode = "compact" if self.display_mode == "full" else "full"
        return {"display_mode": self.display_mode}

    @XBlock.json_handler
    def reset_answer(self, data, suffix=''):
        """Reset the student's answer and attempts (Scope.user_state only)."""
        if not self.allow_reset:
            return {"success": False, "error": "Reset not allowed"}

        self.student_answer = ""
        self.is_submitted = False
        self.score_earned = 0.0
        self.attempts_used = 0
        self.student_data = None
        self.hint_index = 0

        return {"success": True}

    @XBlock.json_handler
    def show_hint(self, data, suffix=''):
        """Return the next hint from the hints list."""
        if not self.hints:
            return {"hint": None, "message": "No hints available"}

        if self.hint_index >= len(self.hints):
            return {"hint": None, "message": "All hints shown"}

        hint = self.hints[self.hint_index]
        self.hint_index += 1

        return {
            "hint": hint,
            "hints_remaining": len(self.hints) - self.hint_index,
        }

    @XBlock.handler
    def raw_data_handler(self, request, suffix=''):
        """Raw handler returning a webob.Response (non-JSON handler demo)."""
        response_data = json.dumps({
            "raw_handler": True,
            "block_type": "vladx",
            "usage_id": str(self.scope_ids.usage_id),
            "http_method": request.method,
            "suffix": suffix,
        })

        return Response(
            body=response_data,
            content_type="application/json",
            charset="utf-8",
        )

    # --- Validation ---

    def validate(self):
        """Validate block settings."""
        validation = super().validate()

        if not self.question_text:
            validation.add(
                ValidationMessage(ValidationMessage.ERROR, "Question text cannot be empty.")
            )
        if self.max_attempts < 1:
            validation.add(
                ValidationMessage(ValidationMessage.WARNING, "Max attempts should be at least 1.")
            )
        if self.weight <= 0:
            validation.add(
                ValidationMessage(ValidationMessage.WARNING, "Weight should be a positive number.")
            )

        return validation

    # --- XML/OLX serialization ---

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        """Deserialize block from XML/OLX with custom <explanation> handling."""
        block = runtime.construct_xblock_from_class(cls, keys)

        for name, value in node.items():
            if name == 'xblock-family':
                continue
            if hasattr(block, name):
                field = block.fields.get(name)
                if field:
                    setattr(block, name, field.from_string(value))

        for child_node in node:
            if child_node.tag == "explanation":
                block.explanation = child_node.text or ""
            else:
                block.runtime.add_node_as_child(block, child_node)

        if node.text and node.text.strip():
            block.question_text = node.text.strip()

        return block

    def add_xml_to_node(self, node):
        """Serialize block to XML/OLX with <explanation> as child element."""
        node.tag = self.xml_element_name()
        node.set('xblock-family', self.entry_point)

        skip_fields = {'children', 'parent', 'explanation'}
        for field_name, field in self.fields.items():
            if field_name in skip_fields:
                continue
            if field.is_set_on(self):
                node.set(field_name, field.to_string(field.read_from(self)))

        if self.explanation:
            from lxml import etree
            expl_node = etree.SubElement(node, "explanation")
            expl_node.text = self.explanation

        if self.has_children:
            self.add_children_to_node(node)

    # --- Search indexing ---

    def index_dictionary(self):
        """Return content for search indexing."""
        xblock_body = super().index_dictionary()
        xblock_body.update({
            "content": {
                "display_name": self.display_name,
                "question_text": self.question_text,
            },
            "content_type": "VladX Learning Hub",
        })
        return xblock_body

    # --- Workbench scenarios ---

    @staticmethod
    def workbench_scenarios():
        """Canned scenarios for the XBlock Workbench."""
        return [
            ("VladX -- Basic",
             """<vladx/>"""),

            ("VladX -- Custom settings",
             """<vladx
                    display_name="Handlers question"
                    question_text="Which decorator is used for JSON handlers in XBlock?"
                    correct_answer="json_handler"
                    max_attempts="5"
                    weight="2.0"
                />"""),

            ("VladX -- Multiple blocks",
             """<vertical_demo>
                    <vladx display_name="Question 1"/>
                    <vladx display_name="Question 2"
                           question_text="Which scope stores per-student data?"
                           correct_answer="user_state"/>
                    <vladx display_name="Question 3"
                           question_text="Which class attribute enables children support?"
                           correct_answer="has_children"/>
                </vertical_demo>"""),

            ("VladX -- With children",
             """<vladx display_name="Question with hints">
                    <html_demo><div style="padding: 10px; background: #eef;">
                        <b>Hint:</b> It's a Python method name that returns a Fragment.
                    </div></html_demo>
                </vladx>"""),
        ]


try:
    from xblock.validation import ValidationMessage
except ImportError:
    class ValidationMessage:
        """Fallback if xblock.validation is not available."""
        ERROR = 'error'
        WARNING = 'warning'

        def __init__(self, message_type, message_text):
            self.type = message_type
            self.text = message_text
