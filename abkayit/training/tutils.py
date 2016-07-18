#!-*- coding:utf-8 -*-

import logging
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from abkayit.settings import EMAIL_FROM_ADDRESS, PREFERENCE_LIMIT, ADDITION_PREFERENCE_LIMIT, REQUIRE_TRAINESS_APPROVE, \
    SEND_REPORT, REPORT_RECIPIENT_LIST

from abkayit.models import ApprovalDate
from abkayit.backend import send_email_by_operation_name
from training.models import Course, TrainessCourseRecord, TrainessParticipation, TrainessTestAnswers
from training.forms import ParticipationForm

from userprofile.userprofileops import UserProfileOPS

log = logging.getLogger(__name__)


def get_approve_start_end_dates_for_inst(site, d):
    """

    :param site: aktif etkinliğin sitesi
    :param d: log icin gerekli detaylar
    :return: egitmenin tercih onaylama tarihlerini barındıran bir dictionary geri dondurur.
    """
    dates = {}
    for i in range(1, PREFERENCE_LIMIT + 1):
        try:
            dates[i] = ApprovalDate.objects.get(site=site, preference_order=i, for_instructor=True)
        except:
            log.info("%d tercih sirasina sahip bir ApprovalDate yok" % i, extra=d)
    for i in range(1, ADDITION_PREFERENCE_LIMIT + 1):
        try:
            dates[-i] = ApprovalDate.objects.get(site=site, preference_order=-i, for_instructor=True)
        except:
            log.info("%d tercih sirasina sahip bir ApprovalDate yok" % -i, extra=d)
    return dates


def get_all_approve_start_end_dates_for_inst(site, d):
    """

    :param site: aktif etkinliğin sitesi
    :param d: log icin gerekli detaylar
    :return: egitmenin tercih onaylama tarihlerini barındıran bir dictionary geri dondurur.
    """
    dates = {}
    for i in range(1, PREFERENCE_LIMIT + 1):
        try:
            dates[i] = ApprovalDate.objects.get(site=site, preference_order=i, for_trainess=True)
        except:
            log.info("%d tercih sirasina sahip bir ApprovalDate yok" % i, extra=d)
    for i in range(1, ADDITION_PREFERENCE_LIMIT + 1):
        try:
            dates[-i] = ApprovalDate.objects.get(site=site, preference_order=-i, for_trainess=True)
        except:
            log.info("%d tercih sirasina sahip bir ApprovalDate yok" % -i, extra=d)
    return dates


def get_approve_start_end_dates_for_tra(site, d):
    """
        :param site: aktif etkinliğin sitesi
        :param d: log icin gerekli detaylar
        :return: kursiyerler için tercih onaylama tarihlerinin start_date'i en yakin olan ile end_date'i en son olani doner.
    """
    try:
        dates = ApprovalDate.objects.filter(site=site, for_trainess=True)
        return dates.order_by("start_date").first(), dates.latest("end_date")
    except:
        return None, None


def get_additional_pref_start_end_dates_for_trainess(site, d):
    """

    :param site: aktif etkinliğin sitesi
    :param d: log icin gerekli detaylar
    :return: ek tercih varsa tarihlerini barındıran bir dictionary geri dondurur.
    """
    dates = {}
    for i in range(1, ADDITION_PREFERENCE_LIMIT + 1):
        try:
            dates[-i] = ApprovalDate.objects.get(site=site, preference_order=-i, for_trainess=True)
        except:
            log.info("%d tercih sirasina sahip bir ApprovalDate yok" % -i, extra=d)
    return dates


def get_approved_trainess(course, d):
    """

    :param d: log icin gerekli bilgileri icerir
    :param course: bir kursta onaylanmis kisilerin listesi
    :return: tercih sırasına göre onaylanan kişileri iceren bir dictionary döner.
    """
    trainess = {}
    for i in range(1, PREFERENCE_LIMIT + 1):
        trainess[i] = TrainessCourseRecord.objects.filter(course=course.pk, preference_order=i, approved=True,
                                                          trainess_approved=True).prefetch_related('course')
    for i in range(1, ADDITION_PREFERENCE_LIMIT + 1):
        trainess[-i] = TrainessCourseRecord.objects.filter(course=course.pk, preference_order=-i, approved=True,
                                                           trainess_approved=True).prefetch_related('course')
    return trainess


def get_trainess_by_course(course, d):
    """

    :param d: log icin gerekli bilgileri icerir
    :param course: ilgili kurs
    :return: diger kurslarda onaylanmamış olanların listesini bir dictionary içerisinde döner
    """
    trainess = {}
    for i in range(1, PREFERENCE_LIMIT + 1):
        trainess[i] = TrainessCourseRecord.objects.filter(course=course.pk, preference_order=i).prefetch_related(
            'course')
    for i in range(1, ADDITION_PREFERENCE_LIMIT + 1):
        trainess[-i] = TrainessCourseRecord.objects.filter(course=course.pk, preference_order=-i).prefetch_related(
            'course')
    return trainess


def is_trainess_approved_any_course(userprofile, site, d):
    """

    :param userprofile: kullanici profili
    :param site: aktif site
    :param d: log icin gerekli bilgiler
    :return: kullanicinin kabul edildiği bir kurs var mı yok mu onu verir True/False
    """
    try:
        approvedtrainesscourserecords = TrainessCourseRecord.objects.filter(trainess=userprofile,
                                                                            approved=True,
                                                                            trainess_approved=True,
                                                                            course__site=site,
                                                                            preference_order__gte=0)
        if not len(approvedtrainesscourserecords):
            return True
        return False
    except ObjectDoesNotExist as e:
        log.info('%s kullanicisinin onaylanmis kaydi yok.' % userprofile.user.username, extra=d)
        return False


def save_course_prefferences(userprofile, course_prefs, site, d, answersforcourse=None):
    res = {'status': '-1', 'message': 'error'}
    if len(course_prefs) <= PREFERENCE_LIMIT:
        context = {}
        oldprefs = TrainessCourseRecord.objects.filter(course__site__is_active=True, trainess=userprofile)

        context['oldprefs'] = {}
        is_changed = False
        if oldprefs:
            for oldpref in oldprefs:
                context['oldprefs'][oldpref.preference_order] = {
                    'course_id': oldpref.course.pk,
                    'course_no': oldpref.course.no,
                    'course_name': oldpref.course.name}
            oldprefs.delete()
        else:
            is_changed = True
        try:
            course_records = []
            for i in range(1, len(course_prefs) + 1):
                if context['oldprefs']:
                    if len(context['oldprefs']) != len(course_prefs) or context['oldprefs'][i].get('course_id') != int(
                            course_prefs[str(i)]):
                        is_changed = True
                course = Course.objects.get(id=int(course_prefs[str(i)]))
                course_record = TrainessCourseRecord(trainess=userprofile,
                                                     course=course,
                                                     preference_order=i,
                                                     )
                course_record.save()
                course_records.append(course_record)
                if answersforcourse:
                    answers = answersforcourse.get(course_prefs[str(i)])
                    if answers:
                        tta = TrainessTestAnswers(tcourserecord=course_record)
                        tta.save()
                        tta.answer.add(*answers)
                        tta.save()
            res['status'] = 0
            res['message'] = "Tercihleriniz başarılı bir şekilde güncellendi"
            context['user'] = userprofile.user
            context['course_prefs'] = course_records
            context['site'] = site
            domain = site.home_url
            context['domain'] = domain.rstrip('/')
            try:
                if is_changed:
                    if SEND_REPORT:
                        context['recipientlist'] = REPORT_RECIPIENT_LIST
                        send_email_by_operation_name(context, "notice_for_pref_changes")
                    context['recipientlist'] = [userprofile.user.username]
                    send_email_by_operation_name(context, "preference_saved")
            except:
                log.error("rapor e-postası gönderilemedi", extra=d)
        except Exception as e:
            log.error(e.message, extra=d)
            res['message'] = "Tercihleriniz kaydedilirken hata oluştu"
    else:
        res['message'] = "En fazla " + PREFERENCE_LIMIT + " tane tercih hakkına sahipsiniz"
    return res


def gettestsofcourses(course_prefs):
    tests = {}
    for pref, courses in course_prefs.items():
        course = Course.objects.get(pk=int(courses))
        questions = course.question.all()
        textboxquestion = course.textboxquestion.all()
        if questions or textboxquestion:
            tests[course] = (questions, textboxquestion)
    return tests


def daterange(start_date, end_date):
    """
    Verilen iki tarih aralığında bir 'iterable' nesne oluşturur. for ... in yapisinin icerisinde kullanilmak uzere
    :param start_date: baslangic tarihi
    :param end_date: bitis tarihi
    """
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def getparticipationforms(site, courserecord):
    rows = []
    for date in daterange(site.event_start_date, site.event_end_date):
        try:
            tp = TrainessParticipation.objects.get(courserecord=courserecord.pk, day=str(date))
            rows.append(ParticipationForm(instance=tp, prefix="participation" + str(date.day)))
        except:
            rows.append(ParticipationForm(initial={'courserecord': courserecord.pk, 'day': str(date)},
                                          prefix="participation" + str(date.day)))
    return rows


def is_trainess_approved_anothercourse(trainess, cur_pref_order):
    trainessapprovedprefs = TrainessCourseRecord.objects.filter(trainess=trainess, approved=True,
                                                                course__site__is_active=True)
    for tp in trainessapprovedprefs:
        if cur_pref_order < tp.preference_order:
            '''
                Daha az öncelikli bir kursa kabul edilmişse bu kabulünü False yap
                kursun eğitmenlerini haberdar et.
            '''
            tp.approved = False
            tp.trainess_approved = False
            tp.save()
            tp.course.trainess.remove(tp.trainess)
            return tp
    return None


def applytrainerselections(postrequest, courses, data, d):
    note = ""
    now = timezone.now()
    if UserProfileOPS.is_authorized_inst(data["user"].userprofile):
        sendconsentemail = postrequest.get("send_consent_email", False)
        for course in courses:
            try:
                data["changedprefs"] = []
                data["course"] = course
                approvedr = postrequest.getlist('students' + str(course.pk))
                sendconsentmailprefs = postrequest.getlist('consentmail' + str(course.pk))
                for pref in data['dates']:
                    if data['dates'][pref].start_date <= now <= data['dates'][pref].end_date:
                        allprefs = TrainessCourseRecord.objects.filter(course=course.pk, preference_order=pref)
                        for p in allprefs:
                            if not p.consentemailsent:
                                if str(p.pk) not in approvedr and p.approved:
                                    p.approved = False
                                    p.trainess_approved = False
                                    data["changedprefs"].append(p)
                                elif str(p.pk) in approvedr and not p.approved:
                                    data['approvedpref'] = p
                                    trainess_approved_pref = is_trainess_approved_anothercourse(p.trainess, pref)
                                    if trainess_approved_pref:
                                        data['changedpref'] = trainess_approved_pref
                                        data["recipientlist"] = trainess_approved_pref.course.authorized_trainer.all() \
                                            .values_list('user__username', flat=True)
                                        send_email_by_operation_name(data, "inform_trainers_about_changes")
                                    p.approved = True
                                    p.instapprovedate = now
                                    course.trainess.add(p.trainess)
                                    course.save()
                                    if not REQUIRE_TRAINESS_APPROVE:
                                        p.trainess_approved = True
                                    data["changedprefs"].append(p)
                                if sendconsentemail == "on" and str(p.pk) in sendconsentmailprefs:
                                    if p.preference_order == 1 and p.approved:
                                        data['approvedpref'] = p
                                        data["recipientlist"] = [p.trainess.user.username]
                                        res = send_email_by_operation_name(data, "send_consent_email")
                                        if res == 1:
                                            p.consentemailsent = True
                                p.save()
                                log.debug(p, extra=d)
                note = "Seçimleriniz başarılı bir şekilde kaydedildi."
                if data["changedprefs"]:
                    data["recipientlist"] = data['course'].authorized_trainer.all().values_list('user__username',
                                                                                                flat=True)
                    send_email_by_operation_name(data, "inform_about_changes")
            except Exception as e:
                note = "Beklenmedik bir hata oluştu!"
                log.error(e.message, extra=d)
    else:
        note = "Bu işlemi yapmaya yetkiniz yok!"
    return note
