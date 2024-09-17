pipeline {
  agent any 
    stages {
        stage ('checkout') {
            steps {
                git 'https://github.com/Radhakrishnaaaaa/backend.git'
            }
        }
        
        stage ('SonarQube Analysis') {
            environment {
                scannerHome = tool 'SonarScanner'
            }
            steps {
                withSonarQubeEnv('SonarScanner'){
                    sh ''' ${scannerHome}/bin/sonar-scanner '''
                }
            }
        }
    }
}
