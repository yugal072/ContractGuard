SPEC = """openapi: 3.0.0
info:
  title: ContractGuard Test API
  version: 1.0.0

paths:
  /users:
    get:
      summary: List all users
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  required:
                    - id
                    - name
                    - email
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
                    email:
                      type: string
    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
                - email
              properties:
                name:
                  type: string
                email:
                  type: string
                phone:
                  type: string
      responses:
        '201':
          description: Created
        '400':
          description: Bad request

  /users/{userId}:
    get:
      summary: Get user by ID
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
        '404':
          description: Not found
    delete:
      summary: Delete user
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '204':
          description: Deleted
"""