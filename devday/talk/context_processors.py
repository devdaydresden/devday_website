def committee_member_context_processor(request):
    return {'is_committee_member': request.user.has_perms(('talk.add_vote', 'talk.add_talkcomment'))}
