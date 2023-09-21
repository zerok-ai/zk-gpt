import client
import gptLangchianInference
import pineconeInteraction
from clientServices import postgresClient

langChainInferenceProvider = gptLangchianInference.LangChainInference()
pineconeInteractionProvider = pineconeInteraction.PineconeInteraction()


def generate_and_store_inference(issue_id, incident_id):
    # getting langchain inferences
    custom_data, langchian_inference = get_langchain_inference(issue_id, incident_id)
    inference = langchian_inference['final_summary']

    # vectorize data and push to pinecone
    vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchian_inference, custom_data)

    # store in DB
    postgresClient.insert_or_update_inference_to_db(issue_id, incident_id, inference)

    return inference


def get_langchain_inference(issue_id, incident_id):
    # fetch all the data required for langchian inference
    issue_summary = client.getIssueSummary(issue_id)
    spans_map = client.getSpansMap(issue_id, incident_id)
    exception_map = []
    req_res_payload_map = []
    for span_id in spans_map:
        span_raw_data = client.getSpanRawdata(issue_id, incident_id, span_id)
        spans_map[span_id].update(span_raw_data)

    filtered_spans_map = dict()
    for spanId in spans_map:
        # remove error key from spanMap
        del spans_map[spanId]["error"]

        span = spans_map[spanId]
        span["span_id"] = spanId
        # remove exception span from spanMap
        if str(span["protocol"]).upper() == "EXCEPTION" or str(span["path"]).upper() == "/EXCEPTION":
            parent_span_id = span["parent_span_id"]
            exception_map.append(span["req_body"])
            if parent_span_id in spans_map:
                spans_map[parent_span_id]["exception"] = span["req_body"]
                filtered_spans_map[parent_span_id] = spans_map[parent_span_id]
        else:
            filtered_spans_map[spanId] = span

    for spanId in filtered_spans_map:
        span = spans_map[spanId]
        req_res_payload_map.append({"request_payload": span['req_body'], "span": spanId})
        req_res_payload_map.append({"response_payload": span['resp_body'], "span": spanId})

    # create input variable for langchain
    # exception_temp_data = """{stacktrace=[ai.zerok.order.service.OrderService.checkStockInInventory(OrderService.java:182), ai.zerok.order.service.OrderService.placeOrder(OrderService.java:67), java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method), java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77), java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43), java.base/java.lang.reflect.Method.invoke(Method.java:568), org.springframework.aop.support.AopUtils.invokeJoinpointUsingReflection(AopUtils.java:343), org.springframework.aop.framework.ReflectiveMethodInvocation.invokeJoinpoint(ReflectiveMethodInvocation.java:196), org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:163), org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:752), org.springframework.transaction.interceptor.TransactionInterceptor$1.proceedWithInvocation(TransactionInterceptor.java:123), org.springframework.transaction.interceptor.TransactionAspectSupport.invokeWithinTransaction(TransactionAspectSupport.java:388), org.springframework.transaction.interceptor.TransactionInterceptor.invoke(TransactionInterceptor.java:119), org.springframework.aop.framework.ReflectiveMethodInvocation.proceed(ReflectiveMethodInvocation.java:184), org.springframework.aop.framework.CglibAopProxy$CglibMethodInvocation.proceed(CglibAopProxy.java:752), org.springframework.aop.framework.CglibAopProxy$DynamicAdvisedInterceptor.intercept(CglibAopProxy.java:703), ai.zerok.order.service.OrderService$$SpringCGLIB$$0.placeOrder(<generated>), ai.zerok.order.controller.OrderController.placeOrder(OrderController.java:22), java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method), java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77), java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43), java.base/java.lang.reflect.Method.invoke(Method.java:568), org.springframework.web.method.support.InvocableHandlerMethod.doInvoke(InvocableHandlerMethod.java:207), org.springframework.web.method.support.InvocableHandlerMethod.invokeForRequest(InvocableHandlerMethod.java:152), org.springframework.web.servlet.mvc.method.annotation.ServletInvocableHandlerMethod.invokeAndHandle(ServletInvocableHandlerMethod.java:117), org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.invokeHandlerMethod(RequestMappingHandlerAdapter.java:884), org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerAdapter.handleInternal(RequestMappingHandlerAdapter.java:797), org.springframework.web.servlet.mvc.method.AbstractHandlerMethodAdapter.handle(AbstractHandlerMethodAdapter.java:87), org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1080), org.springframework.web.servlet.DispatcherServlet.doService(DispatcherServlet.java:973), org.springframework.web.servlet.FrameworkServlet.processRequest(FrameworkServlet.java:1011), org.springframework.web.servlet.FrameworkServlet.doPost(FrameworkServlet.java:914), jakarta.servlet.http.HttpServlet.service(HttpServlet.java:731), org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:885), jakarta.servlet.http.HttpServlet.service(HttpServlet.java:814), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:223), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.apache.tomcat.websocket.server.WsFilter.doFilter(WsFilter.java:53), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:185), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.springframework.web.filter.RequestContextFilter.doFilterInternal(RequestContextFilter.java:100), org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:116), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:185), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.springframework.web.filter.FormContentFilter.doFilterInternal(FormContentFilter.java:93), org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:116), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:185), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.springframework.web.servlet.v6_0.OpenTelemetryHandlerMappingFilter.doFilter(OpenTelemetryHandlerMappingFilter.java:76), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:185), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.springframework.web.filter.CharacterEncodingFilter.doFilterInternal(CharacterEncodingFilter.java:201), org.springframework.web.filter.OncePerRequestFilter.doFilter(OncePerRequestFilter.java:116), org.apache.catalina.core.ApplicationFilterChain.internalDoFilter(ApplicationFilterChain.java:185), org.apache.catalina.core.ApplicationFilterChain.doFilter(ApplicationFilterChain.java:158), org.apache.catalina.core.StandardWrapperValve.invoke(StandardWrapperValve.java:177), org.apache.catalina.core.StandardContextValve.invoke(StandardContextValve.java:97), org.apache.catalina.authenticator.AuthenticatorBase.invoke(AuthenticatorBase.java:542), org.apache.catalina.core.StandardHostValve.invoke(StandardHostValve.java:119), org.apache.catalina.valves.ErrorReportValve.invoke(ErrorReportValve.java:92), org.apache.catalina.core.StandardEngineValve.invoke(StandardEngineValve.java:78), org.apache.catalina.valves.RemoteIpValve.invoke(RemoteIpValve.java:741), org.apache.catalina.connector.CoyoteAdapter.service(CoyoteAdapter.java:357), org.apache.coyote.http11.Http11Processor.service(Http11Processor.java:400), org.apache.coyote.AbstractProcessorLight.process(AbstractProcessorLight.java:65), org.apache.coyote.AbstractProtocol$ConnectionHandler.process(AbstractProtocol.java:859), org.apache.tomcat.util.net.NioEndpoint$SocketProcessor.doRun(NioEndpoint.java:1734), org.apache.tomcat.util.net.SocketProcessorBase.run(SocketProcessorBase.java:52), org.apache.tomcat.util.threads.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1191), org.apache.tomcat.util.threads.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:659), org.apache.tomcat.util.threads.TaskThread$WrappingRunnable.run(TaskThread.java:61), java.base/java.lang.Thread.run(Thread.java:833)], message=item not in stock} """
    custom_data = {"issue_data": str(issue_summary["issue_title"]), "trace_data": str(filtered_spans_map),
                   "exception_data": str(exception_map), "req_res_data": str(req_res_payload_map),
                   "issue_prompt": "You are a backend developer AI assistant. Your task is to figure out why an issue happened based the exception,trace,request respone payload data's presented to you in langchain sequential chain manner, and present it in a concise manner."}
    print("----------------custom data--------------------------------------\n")
    print(custom_data)
    # get langchain inference
    langchian_inference = langChainInferenceProvider.get_gpt_langchain_inference(issue_id, incident_id, custom_data)

    return custom_data, langchian_inference


def vectorize_inference_data_and_push_to_pinecone(issue_id, incident_id, langchian_inference, custom_data):
    # push data to pinecone
    pinecone_issue_data = dict()
    pinecone_issue_data['issue_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id, "data",
                                                                                       "issue",
                                                                                         custom_data['issue_data'],
                                                                                       "default", "default")
    pinecone_issue_data['trace_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id, "data",
                                                                                       "trace",
                                                                                         custom_data['trace_data'],
                                                                                       "default", "default")
    pinecone_issue_data['exception_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                           "data",
                                                                                           "exception",
                                                                                             custom_data[
                                                                                               'exception_data'],
                                                                                           "default", "default")
    pinecone_issue_data['req_res_data'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id, "data",
                                                                                         "req_res",
                                                                                           custom_data['req_res_data'],
                                                                                         "default", "default")
    pinecone_issue_data['req_res_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                            "summary", "req_res",
                                                                                              langchian_inference[
                                                                                                'req_res_summary'],
                                                                                            "default",
                                                                                            "default")
    pinecone_issue_data['final_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                          "summary", "final",
                                                                                            langchian_inference[
                                                                                              'final_summary'],
                                                                                          "default",
                                                                                          "default")
    pinecone_issue_data['exception_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                              "summary", "exception",
                                                                                                langchian_inference[
                                                                                                  'exception_summary'],
                                                                                              "default", "default")
    pinecone_issue_data['trace_summary'] = pineconeInteractionProvider.create_pinecone_data(issue_id, incident_id,
                                                                                          "summary", "trace",
                                                                                            langchian_inference[
                                                                                              'trace_summary'],
                                                                                          "default",
                                                                                          "default")
    # pinecone_issue_data['issue_summary'] = pineconeInteractionProvider.createPineconeData(issue_id, incident_id,
    #                                                                                     "summary", "issue",
    #                                                                                     langchian_inference[
    #                                                                                         'issue_summary'], "default",
    #                                                                                     "default")
    data_list = [value for value in pinecone_issue_data.values()]
    pineconeInteractionProvider.vectorize_data_and_pushto_pinecone_db(issue_id, incident_id, data_list)
