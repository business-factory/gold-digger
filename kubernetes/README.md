Important commands:

(key is private key and crt is certifikate + intermediate key)

kubectl create secret tls rh-crt --key tls.key --cert tls.crt 

kubectl create secret docker-registry regsecret --docker-server='http://***.***' --docker-username='***' --docker-password="***" --docker-email='***'

kubectl create secret generic golddigger-access-key --from-literal=secret='***'

kubectl create secret generic golddigger-secret --from-literal=username='***' --from-literal=password='***'
