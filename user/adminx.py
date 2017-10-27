import xadmin
from xadmin import views
from xadmin.plugins.auth import UserAdmin
from .models import User


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True


class GlobalSettings(object):
    site_title = "Oasis"
    site_footer = "Oasis"
    # menu_style = "accordion"


class MyUserAdmin(UserAdmin):
    list_display = ['username', ]


xadmin.site.unregister(User)
xadmin.site.register(User, MyUserAdmin)
xadmin.site.register(views.BaseAdminView, BaseSetting)
xadmin.site.register(views.CommAdminView, GlobalSettings)
