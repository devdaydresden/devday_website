def committee_member_context_processor(request):
    if request.user.is_authenticated:
        return {'is_committee_member': request.user.has_perms(
            ('talk.add_vote', 'talk.add_talkcomment'))}
    else:
        return {'is_committee_member': False}
