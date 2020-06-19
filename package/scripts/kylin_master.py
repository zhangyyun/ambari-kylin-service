import os
import base64
from time import sleep
from resource_management import *

class KylinMaster(Script):
    
    def install(self, env):      
        import params
        self.install_packages(env)
        
        User(params.kylin_user)
        Directory([params.install_dir],
              owner=params.kylin_user,
              mode=0755,
              cd_access='a',
              create_parents=True,
              recursive_ownership=True
        )
        
        Execute('cd ' + params.install_dir + '; wget ' + params.downloadlocation + ' -O kylin.tar.gz  ', user=params.kylin_user)
        Execute('cd ' + params.install_dir + '; tar -xvf kylin.tar.gz', user=params.kylin_user)
        Execute('cd ' + params.install_dir + ';rm -rf latest; ln -s apache-kylin* latest', user=params.kylin_user)
        
        #mkdir
        Execute('sudo -uhdfs hadoop fs -mkdir -p /kylin')
        Execute('sudo -uhdfs hadoop fs -chown -R kylin:kylin /kylin')

    def configure(self, env):  
        import params
        params.server_mode="all"
        env.set_params(params)
        kylin_properties = InlineTemplate(params.kylin_properties)   
        File(format("{install_dir}/latest/conf/kylin.properties"), content=kylin_properties, owner=params.kylin_user)
        
        File(format("{tmp_dir}/kylin_init.sh"),
             content=Template("init.sh.j2"),
             mode=0o700,
             owner=params.kylin_user
             )        
        File(format("{tmp_dir}/kylin_env.rc"),
             content=Template("env.rc.j2"),
             mode=0o700,
             owner=params.kylin_user
             )              
        Execute(format("bash {tmp_dir}/kylin_init.sh"), user=params.kylin_user)
             
    def start(self, env):
        import params
        env.set_params(params)
        self.configure(env)
        Execute(format(". {tmp_dir}/kylin_env.rc;{install_dir}/latest/bin/kylin.sh start"),
            user=params.kylin_user)
        sleep(5)
        Execute("ps -ef | grep java | grep kylin | grep -v grep | awk '{print $2}' >"+format("{install_dir}/latest/pid"))
        Execute(format("rm -rf /var/run/kylin.pid;cp {install_dir}/latest/pid /var/run/kylin.pid"))
        

    def stop(self, env):
        import params
        env.set_params(params)
        self.configure(env)
        Execute(format(". {tmp_dir}/kylin_env.rc;{install_dir}/latest/bin/kylin.sh stop"),
            user=params.kylin_user)

    def restart(self, env):
        self.stop(env)
        self.start(env)

    def status(self, env):
        check_process_status("/var/run/kylin.pid")


if __name__ == "__main__":
    KylinMaster().execute()
