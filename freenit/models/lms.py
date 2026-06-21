from freenit.config import getConfig

config = getConfig()
lms = config.get_model("lms")

Course = lms.Course
CourseOptional = lms.CourseOptional
Lecture = lms.Lecture
LectureOptional = lms.LectureOptional
LectureState = lms.LectureState
CourseGroup = lms.CourseGroup
CourseGroupOptional = lms.CourseGroupOptional
CourseGroupPermission = lms.CourseGroupPermission
CourseMember = lms.CourseMember
NotFoundError = lms.NotFoundError
IntegrityError = lms.IntegrityError
