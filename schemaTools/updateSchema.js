/**
 * Updates the CRD file generating a K8S CRD openAPIV3Schema from a JSON-Schema.
 */

const fs = require('fs');
const yaml = require('js-yaml');
const toOpenApi = require('json-schema-to-openapi-schema');
const $RefParser = require("@apidevtools/json-schema-ref-parser");

// Clean keys in object recursively
function removeKey(obj, keyNames) {
    for (prop in obj) {
        if (keyNames.includes(prop)) {
            delete obj[prop];
        }
        else if (typeof obj[prop] === 'object')
            removeKey(obj[prop], keyNames);
    }
}

function updateCRDFile(crdFilename, jsonSchemaFilename) {
    let jsonSchema = yaml.safeLoad(fs.readFileSync(jsonSchemaFilename, 'utf8'));
    let crd = yaml.safeLoad(fs.readFileSync(crdFilename, 'utf8'));
    $RefParser.dereference(jsonSchema, (err, schemaDereferenced) => {
        if (err) {
            console.error(err);
        }
        else {
            const openApiSchema = toOpenApi(schemaDereferenced);
            scenarioSchema = openApiSchema.properties.scenarios.items
            removeKey(scenarioSchema, ["additionalProperties", "default"])
            var validationSchema = {
                "type": "object",
                "required": ["spec"],
                "properties": {
                    "spec": scenarioSchema
                }
            }
            crd.spec.validation.openAPIV3Schema = validationSchema
            let yamlStr = yaml.safeDump(crd);
            fs.writeFileSync(crdFilename, yamlStr, 'utf8');
        }
    })
}

updateCRDFile('../kubernetes/crd.yaml', '../powerfulseal/policy/ps-schema.yaml')
