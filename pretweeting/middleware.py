from django.db import connection
from django.template import Template, Context

from django.conf import settings
from django.utils.cache import patch_vary_headers

class MultiHostMiddleware:

    def process_request(self, request):
        try:
            if request.META["HTTP_HOST"].startswith('data.'):
                # use the data URLCONF
                request.urlconf = 'pretweeting.views.data.urls'
        except KeyError:
            pass # use default urlconf (settings.ROOT_URLCONF)

    def process_response(self, request, response):
        if getattr(request, "urlconf", None):
            patch_vary_headers(response, ('Host',))
        return response

class SQLLogMiddleware:

    def process_response(self, request, response):
        
        time = 0.0
        for q in connection.queries:
            time += float(q['time'])

        t = Template("""
            <p><em>Total query count:</em> {{ count }}<br/>
            <em>Total execution time:</em> {{ time }}</p>
            <ul>
                {% for sql in sqllog %}
                    <li class="debug_sql_query">
                        {{ sql.time }}: {{ sql.sql }}
                    </li>
                {% endfor %}
            </ul>
        """)

        context = Context({
            'sqllog': connection.queries, 
            'count': len(connection.queries), 
            'time': time
        })
        output = t.render(context)
        
        response.content = response.content.replace(
                "<!-- sql_log -->", str(output))
        
        return response

class PrintSQLLogMiddleware:

    def process_response(self, request, response):
        if not connection.queries:
            return response
        
        time = 0.0
        for q in connection.queries:
            time += float(q['time'])

        print 'Total query count: %d' % len(connection.queries)
        print 'Total query time: %.3f' % time
        # for q in connection.queries:
        #     print '%.3f: %s' % (float(q['time']), q['sql'])

        return response